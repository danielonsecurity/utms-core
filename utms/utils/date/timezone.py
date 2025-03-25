from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional


def get_timezone_from_seconds(seconds: Decimal) -> timezone:
    """Create a timezone object from seconds offset.

    Args:
        seconds: Timezone offset in seconds

    Returns:
        datetime.timezone object with the specified offset
    """
    return timezone(timedelta(seconds=int(seconds)))


def get_datetime_from_timestamp(timestamp: Decimal, tz: Optional[timezone] = None) -> datetime:
    """Create a datetime object from timestamp and timezone.

    Args:
        ts: Unix timestamp
        tz: Optional timezone object (defaults to UTC if None)

    Returns:
        datetime.datetime object for the given timestamp and timezone
    """
    return datetime.fromtimestamp(float(timestamp), tz=tz if tz is not None else timezone.utc)
