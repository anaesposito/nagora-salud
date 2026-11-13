import json
import os
import tempfile
import threading
import unittest
from contextlib import closing
from http.client import HTTPConnection
from pathlib import Path
from uuid import uuid4
from unittest.mock import patch

from domain import today, money, connect
from server import make_server

class Client:
    def __init__(self, server):
        self.server = server
        self.cookie = ''

    def call(self, path, data=None, expected=200, origin=None):
        connection = HTTPConnection('127.0.0.1', self.server.server_port, timeout=5)
        headers = {'Cookie': self.cookie}
        if data is not None:
            headers.update({'Origin':origin or self.server.origin,'Content-Type':'application/json'})
            data = json.dumps({'key':str(uuid4()),**data})
        connection.request('GET' if data is None else 'POST',path,data,headers)
        response = connection.getresponse()
        raw = response.read()
        if response.getheader('Set-Cookie'):
            self.cookie = response.getheader('Set-Cookie').split(';')[0]
        connection.close()
        if response.status != expected:
            raise AssertionError((path,response.status,raw))
        return json.loads(raw) if 'application/json' in response.getheader('Content-Type') else raw

class NagoraTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name)/'test.sqlite'
        with patch.dict(os.environ, {'NAGORA_DEMO_ONLY':'0', 'RENDER':'false', 'RENDER_EXTERNAL_URL':'', 'NAGORA_ORIGIN':''}):
            self.server = make_server(self.path,port=0)
        self.thread = threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()
        self.client = Client(self.server)
        self.credentials = dict(email='a@example.test',password='una clave larga',name='Ana')
        self.client.call('/api/register',self.credentials)
        self.when = today().isoformat()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.tmp.cleanup()

    def state(self):
        return self.client.call('/api/state')

    def movement(self, **changes):
        data=dict(kind='income',source='Particular',concept='Consultas',amount='70.000',day=self.when)
        self.client.call('/api/movements',{**data,**changes})
        return self.state()['records'][0]['id']

    def test_demo_and_empty_account(self):
        self.assertEqual(self.state()['totals']['received'],0)
        self.client.call('/api/demo',{})
        totals=self.state()['totals']
        self.assertEqual((totals['received'],totals['pending'],totals['spent'],totals['net']),
                         (245000000,78000000,92000000,153000000))

    def test_paid_income_and_reload(self):
        self.movement(paid=True,paid_day=self.when)
        self.assertEqual(self.state()['totals']['received'],7000000)
        another=Client(self.server)
        another.call('/api/login',self.credentials)
        self.assertEqual(another.call('/api/state')['totals']['received'],7000000)
        self.assertEqual(another.call('/api/state?month=2000-01')['totals']['received'],0)
        self.assertIn(b'Nagora Salud',another.call('/'))

    def test_pending_partial_and_complete(self):
        ident=self.movement()
        self.assertEqual(self.state()['totals']['received'],0)
        self.assertEqual(self.state()['totals']['pending'],7000000)
        path=f'/api/movements/{ident}/settle'
        self.client.call(path,dict(amount='25.000',day=self.when,reason='Pago',key='same-request'))
        self.client.call(path,dict(amount='25.000',day=self.when,reason='Pago',key='same-request'))
        self.assertEqual(self.state()['records'][0]['state'],'Parcialmente cobrado')
        self.assertEqual(self.state()['totals']['pending'],4500000)
        self.client.call(path,dict(amount='45001',day=self.when,reason='Pago'),400)
        self.client.call(path,dict(amount='45000',day=self.when,reason='Pago'))
        self.assertEqual(self.state()['totals']['pending'],0)
        self.assertEqual(self.state()['totals']['received'],7000000)
        self.assertEqual(len(self.state()['records']),1)

    def test_liquidation_adjustment_edit_void(self):
        self.client.call('/api/payers',dict(kind='Prepaga',name='Ejemplo',days='30'))
        payer=self.state()['payers'][0]['id']
        ident=self.movement(source='Prepaga',payer=payer,reference='L001')
        base=f'/api/movements/{ident}'
        self.client.call(base+'/settle',dict(amount='60000',day=self.when,reason='Pago'))
        self.client.call(base+'/settle',dict(amount='10000',day=self.when,reason='Descuento'))
        self.assertEqual(self.state()['totals']['activity'],6000000)
        self.assertEqual(self.state()['totals']['received'],6000000)
        self.assertEqual(self.state()['records'][0]['state'],'Cerrado con ajuste')
        self.client.call(base+'/edit',dict(source='Prepaga',payer=payer,reference='L001',concept='Corregido',amount='70000',day=self.when))
        self.assertEqual(self.state()['records'][0]['concept'],'Corregido')
        self.client.call(base+'/void',dict(note='Carga errónea'))
        self.assertEqual(self.state()['records'][0]['state'],'Anulado')
        self.assertEqual(self.state()['totals']['received'],0)
        with closing(connect(self.path)) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM audit').fetchone()[0],5)

    def test_recurring_expense_settlement_and_reminder(self):
        ident=self.movement(kind='expense',source='Alquiler',amount='10000,05',day='2026-01-31',recurrence=True)
        rows=self.state()['records']
        self.assertTrue(any(r['day']=='2026-02-28' for r in rows))
        self.assertEqual(len(rows),len(self.state()['records']))
        current=next(r for r in rows if r['day'].startswith(self.when[:7]))
        path=f"/api/movements/{current['id']}"
        self.client.call(path+'/remind',dict(day=self.when,note='Revisar el alquiler'))
        self.assertEqual(len(self.state()['reminders']),1)
        self.client.call(path+'/settle',dict(amount='10000,05',day=self.when,reason='Pago'))
        self.assertEqual(self.state()['totals']['spent'],1000005)
        self.assertEqual(len(rows),len(self.state()['records']))

    def test_password_recovery_revokes_sessions_and_code(self):
        code=self.client.call('/api/recovery',dict(password=self.credentials['password']))['code']
        other=Client(self.server)
        new_password='una nueva clave larga'
        data=dict(email=self.credentials['email'],password=new_password,code=code)
        other.call('/api/reset',data)
        self.client.call('/api/state',expected=401)
        other.call('/api/reset',data,400)
        other.call('/api/login',dict(email=data['email'],password=new_password))
        self.assertEqual(other.call('/api/state')['profile']['name'],'Ana')

    def test_isolation_and_validation(self):
        ident=self.movement()
        other=Client(self.server)
        other.call('/api/register',dict(email='b@example.test',name='Otra',password='una clave larga'))
        self.assertEqual(other.call('/api/state')['records'],[])
        other.call(f'/api/movements/{ident}/void',dict(note='Cruce'),404)
        self.client.call('/api/profile',dict(name='Cambio'),403,origin='https://example.test')
        self.client.call('/api/movements',dict(kind='income',source='Particular',concept='Consultas',amount='70000',day=self.when),400)
        self.client.call('/api/logout',{})
        self.client.call('/api/state',expected=401)
        self.assertEqual(money('70.000,05'),7000005)
        for value in ('-1','0','2,345','1e4','1.25'):
            with self.assertRaises(ValueError):
                money(value)

if __name__=='__main__':
    unittest.main()
