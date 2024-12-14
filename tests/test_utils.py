import unittest
from unittest.mock import patch
from io import StringIO
from datetime import datetime, timezone

from utms.utils import get_current_time_ntp, print_time

local_timezone = datetime.now().astimezone().tzinfo


class TestPrintFunction(unittest.TestCase):
    @patch("sys.stdout", new_callable=StringIO)
    def test_prints_current_time_ntp(self, mock_stdout):
        print_time(get_current_time_ntp())
        output = mock_stdout.getvalue()
        self.assertTrue(output.strip(), "Function did not print anything!")

    @patch("sys.stdout", new_callable=StringIO)
    def test_prints_time_ntp(self, mock_stdout):
        print_time(datetime(1950, 1, 1, 0, 0, tzinfo=timezone.utc))
        output = mock_stdout.getvalue()
        self.assertTrue(output.strip(), "Function did not print anything!")


if __name__ == "__main__":
    unittest.main()
