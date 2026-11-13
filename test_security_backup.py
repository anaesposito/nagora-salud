import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from backup import copy_database
from domain import connect, initialize, money, snapshot
from server import allow_auth, AUTH_WINDOW
import test_app


class AuthTests(unittest.TestCase):
    setUp = test_app.NagoraTests.setUp
    tearDown = test_app.NagoraTests.tearDown
    state = test_app.NagoraTests.state
    movement = test_app.NagoraTests.movement

    def test_recovery_expiry_and_replacement(self):
        first = self.client.call('/api/recovery', {'password':self.credentials['password']})
        second = self.client.call('/api/recovery', {'password':self.credentials['password']})
        data = dict(email=self.credentials['email'], password='replacement password')
        self.client.call('/api/reset', dict(data, code=first['code']), 400)
        with closing(connect(self.path)) as db, db:
            db.execute('UPDATE recovery SET expires=0')
        self.client.call('/api/reset', dict(data, code=second['code']), 400)
        self.assertEqual(self.state()['profile']['name'], 'Ana')

    def test_session_expiry(self):
        with closing(connect(self.path)) as db, db:
            db.execute('UPDATE session SET expires=0')
        self.client.call('/api/state', expected=401)

    def test_http_throttles_before_password_hash(self):
        with patch('server.valid_password', return_value=False) as verify:
            for _ in range(19):
                self.client.call('/api/login', self.credentials, 400)
            self.client.call('/api/login', self.credentials, 429)
            self.assertEqual(verify.call_count, 19)

    def test_restore_preserves_finances_and_revokes_credentials(self):
        self.movement(amount='100,01', paid=True, paid_day=self.when)
        self.client.call('/api/recovery', {'password':self.credentials['password']})
        backup = Path(self.tmp.name) / 'backup.sqlite'
        restored = Path(self.tmp.name) / 'restored.sqlite'
        copy_database(self.path, backup)
        copy_database(backup, restored, restore=True)
        with closing(connect(restored)) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM session').fetchone()[0], 0)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM recovery').fetchone()[0], 0)
            self.assertEqual(snapshot(db, 1, self.when[:7])[1]['received'], 10001)
        self.assertEqual(self.state()['totals']['received'], 10001)
        with self.assertRaises(FileExistsError):
            copy_database(backup, self.path, restore=True)


class LimiterTests(unittest.TestCase):
    def test_persistent_concurrent_window_and_ip_budget(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'test.sqlite'
            initialize(path)
            with ThreadPoolExecutor(max_workers=8) as pool:
                results = list(pool.map(lambda _: allow_auth(path, 'local', 'A@EXAMPLE.TEST', now=1000), range(30)))
            self.assertEqual(sum(results), 20)
            self.assertFalse(allow_auth(path, 'other-ip', ' a@example.test ', now=1001))
            self.assertTrue(allow_auth(path, 'local', 'a@example.test', now=1000 + AUTH_WINDOW))
            for _ in range(99):
                self.assertTrue(allow_auth(path, 'local', None, now=1000 + AUTH_WINDOW))
            self.assertFalse(allow_auth(path, 'local', None, now=1000 + AUTH_WINDOW))

    def test_legacy_recovery_migration_is_repeatable(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'test.sqlite'
            with closing(connect(path)) as db, db:
                db.execute('CREATE TABLE recovery(owner INTEGER PRIMARY KEY, digest TEXT NOT NULL)')
                db.execute("INSERT INTO recovery VALUES(1,'old')")
            initialize(path)
            initialize(path)
            with closing(connect(path)) as db:
                self.assertEqual(db.execute('SELECT expires FROM recovery').fetchone()[0], 0)

    def test_corrupt_backup_never_leaves_destination(self):
        with tempfile.TemporaryDirectory() as folder:
            source, target = Path(folder) / 'bad.sqlite', Path(folder) / 'new.sqlite'
            source.write_text('not a database')
            with self.assertRaises(Exception):
                copy_database(source, target)
            self.assertFalse(target.exists())

    def test_money_boundary_exact(self):
        self.assertEqual(money('99.999.999.999,99'), 9999999999999)
        self.assertEqual(money('0,01'), 1)
        for value in ('NaN', 'Infinity', '100000000000', '1,001', True, None):
            with self.assertRaises(ValueError):
                money(value)
