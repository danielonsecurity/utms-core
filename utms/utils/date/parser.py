from datetime import datetime, timezone
from typing import Optional

import dateparser


def parse_date_to_utc(input_text: str) -> Optional[datetime]:
    """Parses a string into UTC datetime."""
    parsed_date = dateparser.parse(input_text, settings={"RETURN_AS_TIMEZONE_AWARE": True})

    if parsed_date:
        return parsed_date.astimezone(timezone.utc)

    return None
