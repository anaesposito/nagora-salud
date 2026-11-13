import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfoNotFoundError

from domain import argentina_timezone, today
from server import make_server


class TimezoneTests(unittest.TestCase):
    def test_argentina_timezone_available(self):
        self.assertEqual(argentina_timezone().key, 'America/Argentina/Buenos_Aires')
        self.assertEqual(len(today().isoformat()), 10)

    def test_missing_timezone_fails_before_database_or_socket(self):
        with patch('domain.ZoneInfo', side_effect=ZoneInfoNotFoundError('missing')):
            with patch('server.initialize') as initialize:
                with self.assertRaisesRegex(RuntimeError, 'pip install -r requirements.txt'):
                    make_server('unused.sqlite', port=0)
                initialize.assert_not_called()
