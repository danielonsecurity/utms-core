import unittest
from datetime import datetime, timezone
from io import StringIO
from unittest.mock import patch

from utms.config import Config
from utms.utils import *

local_timezone = datetime.now().astimezone().tzinfo
config = Config()


class TestPrintFunction(unittest.TestCase):
    @patch("sys.stdout", new_callable=StringIO)
    def test_prints_time_ntp(self, mock_stdout):
        print_time(datetime(1950, 1, 1, 0, 0, tzinfo=timezone.utc), config)
        output = mock_stdout.getvalue()
        self.assertTrue(output.strip(), "Function did not print anything!")


def test_get_seconds_since_midnight_noon():
    # Mock datetime.now() to return 12:00:00
    mock_time = datetime(2025, 1, 3, 12, 25, 40)

    with patch("utms.utils.datetime") as mock_datetime:
        mock_datetime.now.return_value = mock_time
        seconds = get_seconds_since_midnight()
        expected_seconds = 12 * 3600 + 25 * 60 + 40
        assert seconds == expected_seconds
