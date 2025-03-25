from datetime import datetime
from typing import Optional

from utms.utils.date.parser import parse_date_to_utc
from utms.utils.display.colors import ColorFormatter


def print_parsed_date(input_text: str) -> Optional[datetime]:
    """Parses and prints a date with formatting."""
    parsed_date = parse_date_to_utc(input_text)
    if parsed_date:
        print(ColorFormatter.red(f"dateparser: {parsed_date}"))
    return parsed_date
