import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from datetime import date
from unittest.mock import patch

from domain import connect, repeat_expenses
import test_app


class FinancialEdges(unittest.TestCase):
    setUp = test_app.NagoraTests.setUp
    tearDown = test_app.NagoraTests.tearDown
    state = test_app.NagoraTests.state
    movement = test_app.NagoraTests.movement

    def test_concurrent_same_payment_is_applied_once(self):
        ident = self.movement(amount='100,03')
        data = dict(key='parallel-payment', amount='33,01', day=self.when, reason='Pago')
        def pay(_):
            client = test_app.Client(self.server)
            client.cookie = self.client.cookie
            return client.call(f'/api/movements/{ident}/settle', data)
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(pay, range(4)))
        record = self.state()['records'][0]
        self.assertEqual(record['cash'], 3301)
        self.assertEqual(record['balance'], 6702)
        self.assertEqual(len(record['settlements']), 1)

    def test_cash_month_differs_from_service_month(self):
        ident = self.movement(amount='100,03', day='2020-01-31')
        self.client.call(f'/api/movements/{ident}/settle', dict(amount='33,01', day='2020-02-01', reason='Pago'))
        self.client.call(f'/api/movements/{ident}/settle', dict(amount='0,02', day='2020-02-02', reason='Descuento'))
        january = self.client.call('/api/state?month=2020-01')['totals']
        february = self.client.call('/api/state?month=2020-02')['totals']
        self.assertEqual((january['received'], january['activity']), (0, 10003))
        self.assertEqual((february['received'], february['activity']), (3301, -2))
        self.assertEqual(february['pending'], 6700)

    def test_leap_year_recurrence_and_repeated_materialization(self):
        with patch('domain.today', return_value=date(2024, 2, 10)):
            self.movement(kind='expense', source='Alquiler', amount='0,01', day='2024-01-31', recurrence=True)
            rows = self.state()['records']
            self.assertEqual(sorted(r['day'] for r in rows), ['2024-01-31','2024-02-29','2024-03-31'])
            with closing(connect(self.path)) as db, db:
                repeat_expenses(db, 1)
                repeat_expenses(db, 1)
            self.assertEqual(len(self.state()['records']), 3)

    def test_failed_settlement_can_retry_same_idempotency_key(self):
        ident = self.movement(amount='0,03')
        path = f'/api/movements/{ident}/settle'
        self.client.call(path, dict(key='retry', amount='0,04', day=self.when, reason='Pago'), 400)
        self.client.call(path, dict(key='retry', amount='0,03', day=self.when, reason='Pago'))
        self.assertEqual(self.state()['records'][0]['balance'], 0)
