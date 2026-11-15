import json
import sqlite3
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path

from domain import ROOT, connect, initialize, money
import test_app


class PaymentAmountTests(unittest.TestCase):
    def test_exact_cents_and_supported_bounds(self):
        self.assertEqual(money('0,01'), 1)
        self.assertEqual(money('99999999999,99'), 9999999999999)
        for amount in ('0', '-0,01', '0,001', '100000000000,00', '1e2', True):
            with self.subTest(amount=amount), self.assertRaises(ValueError):
                money(amount)

    def test_migration_preserves_original_payments_and_is_repeatable(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'legacy.sqlite'
            with closing(connect(path)) as db, db:
                db.executescript((ROOT / 'migrations/001.sql').read_text())
                db.execute("INSERT INTO account VALUES(1,'a@example.test','Ana','',0)")
                db.execute("""INSERT INTO movement(id,owner,kind,source,concept,amount,day)
                    VALUES(1,1,'income','Particular','Ejemplo',500,'2020-01-01')""")
                db.execute("INSERT INTO settlement VALUES(9,1,1,'2020-01-01',123,'Pago')")
            initialize(path)
            initialize(path)
            with closing(connect(path)) as db:
                row = db.execute('SELECT id,amount,version FROM effective_settlement').fetchone()
                self.assertEqual(tuple(row), (9,123,0))
                self.assertEqual(db.execute('PRAGMA foreign_key_check').fetchall(), [])


class PaymentRevisionTests(unittest.TestCase):
    setUp = test_app.NagoraTests.setUp
    tearDown = test_app.NagoraTests.tearDown
    state = test_app.NagoraTests.state
    movement = test_app.NagoraTests.movement

    def payment(self, amount='25,01', date='2020-02-01'):
        ident = self.movement(amount='100,10', day='2020-01-01')
        self.client.call(f'/api/movements/{ident}/settle', dict(amount=amount, day=date, reason='Pago'))
        row = self.state()['records'][0]
        return f'/api/movements/{ident}', row['settlements'][0]['id']

    def test_correct_and_reverse_only_one_partial_payment(self):
        base, payment = self.payment()
        self.client.call(base+'/settle', dict(amount='40,07', day='2020-03-02', reason='Pago'))
        self.client.call(base+'/settle', dict(amount='9,02', day='2020-03-02', reason='Descuento'))
        path = f'{base}/payments/{payment}'
        self.client.call(path+'/correct', dict(amount='50,01', day='2020-03-03', version=0, note='Importe y fecha'))
        feb = self.client.call('/api/state?month=2020-02')
        mar = self.client.call('/api/state?month=2020-03')
        self.assertEqual(feb['totals']['received'], 0)
        self.assertEqual(mar['totals'], dict(received=9008, pending=100, spent=0, activity=-902, net=9008,generated=0,discounts=902,retained=0))
        self.client.call(path+'/reverse', dict(version=1, note='Registro duplicado'))
        mar = self.client.call('/api/state?month=2020-03')
        self.assertEqual(mar['totals'], dict(received=4007,pending=5101,spent=0,activity=-902,net=4007,generated=0,discounts=902,retained=0))
        record = mar['records'][0]
        self.assertEqual(record['state'], 'Parcialmente cobrado')
        self.assertFalse(record['void'])
        self.assertEqual([(x['version'],x['amount']) for x in record['payment_history'] if x['payment']==payment],
                         [(0,2501),(1,5001),(2,None)])
        initialize(self.path)
        other = test_app.Client(self.server)
        other.call('/api/login', self.credentials)
        self.assertEqual(other.call('/api/state?month=2020-03'),mar)
        with closing(connect(self.path)) as db:
            audit = db.execute("SELECT owner,details,created FROM audit WHERE action='payment_reverse'").fetchone()
            self.assertEqual(audit['owner'],1)
            self.assertTrue(audit['created'])
            details = json.loads(audit['details'])
            self.assertEqual((details['before']['amount'],details['after'],details['note']), (5001,None,'Registro duplicado'))
            for table in ('settlement','audit','payment_revision'):
                for query in (f'DELETE FROM {table}', f'UPDATE {table} SET owner=owner'):
                    with self.subTest(query=query), self.assertRaises(sqlite3.IntegrityError):
                        db.execute(query)

    def test_validation_account_isolation_and_sessions(self):
        base, payment = self.payment()
        path = f'{base}/payments/{payment}'
        change = dict(version=0,note='Rectificación',amount='26,01',day='2020-02-01')
        for changes in (dict(note=' '),dict(note='a'*121),dict(day='9999-01-01'),dict(version=True),
                        dict(amount='100,11'),dict(amount='0,001'),dict(amount='0'),dict(amount='25,01')):
            self.client.call(path+'/correct',{**change,**changes},400)
        self.client.call(path+'/reverse',dict(version=0),400)
        other = test_app.Client(self.server)
        other.call('/api/demo',{})
        for action in ('correct','reverse'):
            other.call(path+'/'+action,change,404)
        self.assertEqual(self.state()['records'][0]['cash'],2501)
        other.call('/api/logout',{})
        other.call(path+'/reverse',change,401)
        with closing(connect(self.path)) as db, db:
            db.execute('UPDATE session SET expires=0')
        self.client.call(path+'/correct',change,401)
        self.client.call('/api/login',self.credentials)
        self.client.call(path+'/correct',{**change,'amount':'100,10'})
        self.assertEqual(self.state()['records'][0]['state'],'Cobrado')
        self.client.call(path+'/reverse',dict(version=1,note='Reversión total'))
        self.assertEqual(self.state()['records'][0]['state'],'Por cobrar')
        self.client.call(path+'/reverse',dict(version=2,note='Otra reversión'),409)

    def test_other_movement_adjustment_and_void_are_rejected(self):
        base, payment = self.payment()
        second = self.movement(concept='Otro ingreso')
        change = dict(version=0,note='Rectificar')
        self.client.call(f'/api/movements/{second}/payments/{payment}/reverse',change,404)
        self.client.call(base+'/settle',dict(amount='1',day=self.when,reason='Descuento'))
        adjustment = next(s for s in self.state()['records'][-1]['settlements'] if s['reason']=='Descuento')
        self.client.call(f"{base}/payments/{adjustment['id']}/reverse",change,404)
        self.client.call(base+'/void',dict(note='Anulación'))
        self.client.call(f'{base}/payments/{payment}/reverse',change,409)

    def test_same_key_replays_and_concurrent_stale_version_conflicts(self):
        base, payment = self.payment()
        path = f'{base}/payments/{payment}'
        data = dict(version=0,note='Ajuste',amount='30,02',day=self.when,key='payment-test')
        gate = threading.Barrier(2)

        def submit(route, changes, expected):
            client = test_app.Client(self.server)
            client.cookie = self.client.cookie
            gate.wait(timeout=5)
            return client.call(route,changes,expected)

        with ThreadPoolExecutor(2) as pool:
            futures = [pool.submit(submit,path+'/correct',data,200) for _ in range(2)]
            self.assertEqual([f.result() for f in futures],[{'ok':True}]*2)
        self.client.call(path+'/correct',{**data,'amount':'30,03'},409)
        self.client.call(base+'/settle',{**data,'reason':'Pago'},409)
        gate.reset()
        with ThreadPoolExecutor(2) as pool:
            futures = [pool.submit(submit,path+'/reverse',dict(version=1,note='Duplicado',key=f'reverse-{i}'),(200,409))
                       for i in range(2)]
            self.assertEqual(sorted('ok' in f.result() for f in futures),[False,True])
        self.client.call(path+'/correct',data)
        self.assertEqual(self.state()['records'][0]['cash'],0)
        self.assertEqual(len(self.state()['records'][0]['payment_history']),3)

    def test_failure_rolls_back_revision_and_idempotency_key(self):
        base, payment = self.payment()
        path = f'{base}/payments/{payment}/reverse'
        data = dict(version=0,note='Duplicado',key='retry-rollback')
        with closing(connect(self.path)) as db, db:
            db.execute("""CREATE TRIGGER reject_audit BEFORE INSERT ON audit
                WHEN NEW.action='payment_reverse' BEGIN SELECT RAISE(ABORT,'test failure'); END""")
        self.client.call(path,data,400)
        self.assertEqual(self.state()['records'][0]['cash'],2501)
        with closing(connect(self.path)) as db, db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM payment_revision').fetchone()[0],0)
            self.assertIsNone(db.execute('SELECT 1 FROM request WHERE key=?',(data['key'],)).fetchone())
            db.execute('DROP TRIGGER reject_audit')
        self.client.call(path,data)
        self.assertEqual(self.state()['records'][0]['cash'],0)
