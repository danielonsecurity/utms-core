import io
import logging
import sys

from colorama import Fore, Style


class LogFormatter(logging.Formatter):
    """Formatter for log messages"""

    COLORS = {
        "DEBUG": Fore.BLUE,
        "INFO": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Fore.RED + Style.BRIGHT,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_console = False

    def format(self, record):
        original_levelname = record.levelname
        original_name = record.name
        original_msg = record.msg

        if self.is_console:
            color = self.COLORS.get(record.levelname, "")
            record.levelname = f"{color}{record.levelname}{Style.RESET_ALL}"
            record.name = f"{Fore.MAGENTA}{record.name}{Style.RESET_ALL}"
            record.msg = f"{record.msg}"

        result = super().format(record)
        record.levelname = original_levelname
        record.name = original_name
        record.msg = original_msg

        return result
