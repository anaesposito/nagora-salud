import json
import os
import sqlite3
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from domain import connect, initialize, today
from liquidations import amount
from server import make_server
from test_app import Client

class LiquidationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/'db.sqlite'
        with patch.dict(os.environ, {'NAGORA_DEMO_ONLY':'0','RENDER':'false','RENDER_EXTERNAL_URL':'','NAGORA_ORIGIN':''}):
            self.server=make_server(self.path,port=0)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.client=Client(self.server);self.client.call('/api/register',dict(email='a@example.test',password='a long password',name='Ana'))
        self.when=today().isoformat()
        self.client.call('/api/payers',dict(kind='Obra social',name='Entidad ficticia',days=45))
        self.payer=self.state()['payers'][0]['id']
        self.ids=[]
        for i,value in enumerate(['100,01','200,02']):
            self.client.call('/api/movements',dict(kind='income',source='Obra social',payer=self.payer,concept=f'Prestación {i}',amount=value,day=self.when))
            self.ids.append(self.state()['records'][0]['id'])

    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join();self.tmp.cleanup()

    def state(self):
        return self.client.call('/api/state')

    def payload(self):
        return dict(key=str(uuid4()),payer=self.payer,reference='L-001',day=self.when,method='Transferencia',received='210,02',allocations=[
            dict(movement=self.ids[0],allocated='100,01',cash='80,01',discount='5,00',retained='10,00',difference='5,00',discount_kind='Comisión aceptada',retention_kind='Tributaria',note='Diferencia a consultar'),
            dict(movement=self.ids[1],allocated='150,02',cash='130,01',discount='0',retained='0',difference='20,01',note='Pago parcial'),
        ])

    def test_exact_cents_and_rejections(self):
        self.assertEqual(amount('1.234,56'),123456);self.assertEqual(amount('0,00'),0)
        for value in [1,0.1,True,'-1','1.001,001','1.2','NaN','1e2','',None]:
            with self.assertRaises(ValueError):amount(value)

    def test_multi_partial_and_retention_are_not_cash_or_loss(self):
        before=self.state();p=self.payload();result=self.client.call('/api/liquidations',p)
        state=self.state();t=state['totals']
        self.assertEqual(len(state['records']),2)
        self.assertEqual(t['generated'],30003);self.assertEqual(t['received'],21002)
        self.assertEqual(t['retained'],1000);self.assertEqual(t['discounts'],500)
        self.assertEqual(t['pending'],7501);self.assertEqual(t['activity'],29503)
        self.assertEqual(t['net'],21002)
        self.assertEqual(state['liquidations'][0]['id'],result['id'])
        # Later payment consumes the outstanding amount once; original differences stay historical.
        self.client.call(f'/api/movements/{self.ids[1]}/settle',dict(amount='70,01',day=self.when,reason='Pago'))
        self.assertEqual(self.state()['totals']['pending'],500)
        self.assertEqual(self.state()['liquidations'][0]['allocations'][1]['pending_now'],0)

    def test_idempotency_reference_uniqueness_and_conflicting_key(self):
        p=self.payload();first=self.client.call('/api/liquidations',p)
        self.assertEqual(self.client.call('/api/liquidations',p),first)
        self.client.call('/api/liquidations',{**p,'key':str(uuid4())},409)
        self.client.call('/api/liquidations',{**p,'reference':'L-other'},409)
        with closing(connect(self.path)) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM liquidation_revision').fetchone()[0],1)
            self.assertEqual(db.execute('SELECT count(*) FROM settlement').fetchone()[0],4)

    def test_invalid_allocations_roll_back_everything(self):
        base=self.payload()
        cases=[]
        cases.append({**base,'received':'210,03'})
        cases.append({**base,'allocations':[base['allocations'][0]]*2,'received':'160,02'})
        row={**base['allocations'][1],'allocated':'250,02','difference':'120,01'}
        cases.append({**base,'allocations':[base['allocations'][0],row]})
        cases.append({**base,'allocations':[{**base['allocations'][0],'retention_kind':'Impuesto inventado'},base['allocations'][1]]})
        for p in cases:self.client.call('/api/liquidations',p,(400,409))
        self.assertEqual(self.state()['totals']['received'],0)
        with closing(connect(self.path)) as db:
            for table in ['liquidation','liquidation_revision','liquidation_allocation','settlement']:
                self.assertEqual(db.execute(f'SELECT count(*) FROM {table}').fetchone()[0],0)
            self.assertFalse(db.execute('SELECT 1 FROM request WHERE key=?',(base['key'],)).fetchone())

    def test_cross_account_and_expired_session(self):
        p=self.payload();ident=self.client.call('/api/liquidations',p)['id']
        other=Client(self.server);other.call('/api/register',dict(email='b@example.test',password='a long password',name='Otra'))
        other.call('/api/liquidations',{**p,'key':str(uuid4())},404)
        other.call(f'/api/liquidations/{ident}/correct',{**p,'key':str(uuid4()),'note':'Cambio'},404)
        self.assertEqual(other.call('/api/state')['liquidations'],[])
        other.call('/api/payers',dict(kind='Obra social',name='Propio',days=10))
        foreign=other.call('/api/state')['payers'][0]['id']
        other.call('/api/liquidations',{**p,'payer':foreign,'key':str(uuid4())},404)
        with closing(connect(self.path)) as db,db:db.execute('UPDATE session SET expires=0')
        self.client.call('/api/liquidations',p,401)

    def test_group_correction_and_individual_payment_compatibility(self):
        p=self.payload();ident=self.client.call('/api/liquidations',p)['id'];before=self.state()['liquidations'][0]
        payment=next(r for r in self.state()['records'] if r['id']==self.ids[0])['settlements'][0]
        self.client.call(f'/api/movements/{self.ids[0]}/payments/{payment["id"]}/correct',dict(version=0,note='Importe recibido menor',amount='70,01',day=self.when))
        stale={**p,'key':str(uuid4()),'version':before['version'],'token':before['token'],'note':'Corrección completa'}
        self.client.call(f'/api/liquidations/{ident}/correct',stale,409)
        current=self.state()['liquidations'][0]
        self.assertEqual(current['received'],20002);self.assertEqual(current['allocations'][0]['difference'],1500)
        revision={**stale,'key':str(uuid4()),'token':current['token']}
        self.client.call(f'/api/liquidations/{ident}/correct',revision)
        after=self.state();self.assertEqual(after['totals']['received'],21002)
        self.assertEqual(len(after['liquidations'][0]['history']),2)
        self.assertEqual(self.client.call(f'/api/liquidations/{ident}/correct',revision)['version'],2)
        self.client.call(f'/api/movements/{self.ids[0]}/payments/{payment["id"]}/reverse',dict(version=1,note='Ya reemplazado'),409)
        active=next(r for r in after['records'] if r['id']==self.ids[0])['settlements'][0]
        self.client.call(f'/api/movements/{self.ids[0]}/payments/{active["id"]}/reverse',dict(version=0,note='Cobro no acreditado'))
        self.assertEqual(self.state()['totals']['received'],13001)
        self.assertEqual(self.state()['totals']['retained'],1000)

    def test_no_foreign_payer_no_void_no_expense(self):
        p=self.payload()
        self.client.call(f'/api/movements/{self.ids[1]}/void',dict(note='Duplicado'))
        self.client.call('/api/liquidations',p,400)
        self.assertEqual(self.state()['liquidations'],[])

    def test_zero_cash_reclassification_and_legacy_retention(self):
        row=dict(movement=self.ids[0],allocated='100,01',cash='0',discount='0',retained='100,01',difference='0',retention_kind='Por clasificar',note='Retención a revisar')
        p={**self.payload(),'received':'0','allocations':[row]}
        ident=self.client.call('/api/liquidations',p)['id'];s=self.state()
        self.assertEqual(s['totals']['received'],0);self.assertEqual(s['totals']['activity'],30003)
        self.assertEqual(s['totals']['retained'],10001)
        current=s['liquidations'][0]
        release={**p,'key':str(uuid4()),'version':1,'token':current['token'],'note':'Retención liberada y acreditada',
                 'received':'100,01','allocations':[{**row,'cash':'100,01','retained':'0'}]}
        self.client.call(f'/api/liquidations/{ident}/correct',release)
        self.assertEqual(self.state()['totals']['retained'],0)
        self.assertEqual(self.state()['totals']['received'],10001)
        self.client.call(f'/api/movements/{self.ids[1]}/settle',dict(amount='1',day=self.when,reason='Retención'),400)
        with closing(connect(self.path)) as db,db:
            db.execute("INSERT INTO settlement(owner,movement,day,amount,reason) VALUES(1,?,?,100,'Retención')",(self.ids[1],self.when))
        self.assertEqual(self.state()['totals']['activity'],30003)
        self.assertEqual(self.state()['totals']['retained'],100)

    def test_group_vs_individual_concurrent_correction_and_months(self):
        p=self.payload();p['day']='2020-02-01'
        ident=self.client.call('/api/liquidations',p)['id'];group=self.state()['liquidations'][0]
        payment=next(e for e in group['allocations'][0]['payments'] if e['component']=='cash')
        correction={**p,'key':str(uuid4()),'version':1,'token':group['token'],'note':'Fecha corregida','day':'2020-03-01'}
        calls=[(f'/api/liquidations/{ident}/correct',correction),(f'/api/movements/{self.ids[0]}/payments/{payment["id"]}/correct',dict(amount='70,01',day='2020-03-01',version=0,note='Cobro corregido'))]
        barrier=threading.Barrier(2)
        def post(call):
            c=Client(self.server);c.cookie=self.client.cookie;barrier.wait()
            return c.call(*call,expected=(200,409))
        with ThreadPoolExecutor(2) as pool:results=list(pool.map(post,calls))
        self.assertEqual(sum('error' in r for r in results),1)
        feb=self.client.call('/api/state?month=2020-02')['totals']['received']
        mar=self.client.call('/api/state?month=2020-03')['totals']['received']
        self.assertEqual(feb+mar,self.state()['liquidations'][0]['received'])
        self.assertIn(feb+mar,(21002,20002))

    def test_new_keys_cannot_reuse_existing_payment_and_reference_keys(self):
        p=self.payload();self.client.call('/api/liquidations',p)
        self.client.call(f'/api/movements/{self.ids[1]}/settle',dict(key=p['key'],amount='1',day=self.when,reason='Pago'),409)
        group=self.state()['liquidations'][0]
        cash=next(e for e in group['allocations'][0]['payments'] if e['component']=='cash')
        self.client.call(f'/api/movements/{self.ids[0]}/payments/{cash["id"]}/correct',dict(amount='90,01',day=self.when,version=0,note='Exceso sobre asignación'),400)

    def test_concurrent_replay_and_competing_balance(self):
        p=self.payload()
        def post(payload):
            client=Client(self.server);client.cookie=self.client.cookie
            return client.call('/api/liquidations',payload,(200,409))
        with ThreadPoolExecutor(2) as pool:results=list(pool.map(post,[p,p]))
        self.assertEqual(results[0],results[1])
        # Both new statements compete for the same last 5 pesos on the first prestation.
        row=dict(movement=self.ids[0],allocated='5',cash='5',discount='0',retained='0',difference='0')
        a={**p,'key':str(uuid4()),'reference':'L-2','received':'5','allocations':[row]}
        b={**a,'key':str(uuid4()),'reference':'L-3'}
        with ThreadPoolExecutor(2) as pool:results=list(pool.map(post,[a,b]))
        self.assertEqual(sum('id' in r for r in results),1)
        self.assertEqual(self.state()['totals']['received'],21502)

    def test_immutable_ledger_atomic_failure_and_migration(self):
        p=self.payload()
        with closing(connect(self.path)) as db,db:
            db.execute("CREATE TRIGGER fail_liquidation_audit BEFORE INSERT ON audit WHEN NEW.action='liquidation_create' BEGIN SELECT RAISE(ABORT,'Injected failure'); END")
        self.client.call('/api/liquidations',p,400)
        self.assertEqual(self.state()['liquidations'],[])
        with closing(connect(self.path)) as db,db:db.execute('DROP TRIGGER fail_liquidation_audit')
        self.client.call('/api/liquidations',p)
        before=self.state()['totals'];initialize(self.path);self.assertEqual(self.state()['totals'],before)
        with closing(connect(self.path)) as db:
            for table in ['liquidation','liquidation_revision','liquidation_allocation','liquidation_entry','settlement','payment_revision','audit']:
                # payment_revision has no rows until a correction; covered by PR42 tests.
                if table=='payment_revision':continue
                for sql in [f'DELETE FROM {table}',f'UPDATE {table} SET owner=owner']:
                    with self.assertRaises(sqlite3.IntegrityError):db.execute(sql)
                    db.rollback()

if __name__=='__main__':unittest.main()
