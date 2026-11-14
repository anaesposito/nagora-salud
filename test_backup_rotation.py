import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from backup_worker import run_once, RETENTION
from domain import initialize


class RotationTests(unittest.TestCase):
    def test_only_expired_owned_backups_are_removed_after_success(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / 'source.sqlite'
            initialize(source)
            backup_dir = root / 'backups'
            old = run_once(source, backup_dir)
            now = time.time()
            os.utime(old, (now - RETENTION - 1, now - RETENTION - 1))
            unrelated = backup_dir / 'personal.sqlite'
            unrelated.write_text('keep')
            os.utime(unrelated, (0, 0))
            recent = run_once(source, backup_dir)
            self.assertFalse(old.exists())
            self.assertTrue(unrelated.exists())
            self.assertTrue(recent.exists())
            self.assertTrue(source.exists())
            self.assertEqual(len(list(backup_dir.glob('nagora-*.sqlite'))), 1)

    def test_failed_copy_never_prunes_last_good_backup(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / 'source.sqlite'
            initialize(source)
            old = run_once(source, root / 'backups')
            os.utime(old, (0, 0))
            with patch('backup_worker.copy_database', side_effect=OSError('test failure')):
                with self.assertRaises(OSError):
                    run_once(source, root / 'backups')
            self.assertTrue(old.exists())
