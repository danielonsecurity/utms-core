from datetime import datetime, timezone
from decimal import Decimal
from typing import Union

from utms.core import constants


def get_seconds_since_midnight() -> int:
    """Get the number of seconds that have passed since midnight today."""
    now = datetime.now(datetime.now().astimezone().tzinfo)  # Get the current local time
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    seconds_since_midnight = (now - midnight).seconds
    return seconds_since_midnight


def value_to_decimal(value: Union[Decimal, datetime]) -> Decimal:
    """Converts a value to a `Decimal` representation.

    This function accepts either a `Decimal` value or a `datetime` object. If the input
    is a `datetime`, it converts it into a `Decimal` representation of its timestamp.
    For dates before January 2, year 1 (UTC), it adjusts the timestamp by subtracting
    the number of seconds in a year to handle historical date ranges.

    Args:
        value (Union[Decimal, datetime]): The value to be converted. Can be either:
            - A `Decimal` value (returned as-is).
            - A `datetime` object (converted to `Decimal` timestamp).

    Returns:
        Decimal: The `Decimal` representation of the input value.

    Raises:
        TypeError: If the input value is neither a `Decimal` nor a `datetime`.

    Notes:
        - For historical dates (`datetime` objects earlier than 0001-01-02T00:00:00 UTC),
          an adjustment is made to account for historical date handling.
    """
    if isinstance(value, Decimal):
        return value
    elif isinstance(value, (int, float)):
        return Decimal(value)
    # Convert datetime to Decimal (timestamp)
    if value >= datetime(1, 1, 2, 0, 0, tzinfo=timezone.utc):
        value_as_decimal = Decimal(value.timestamp())
    else:
        value_as_decimal = Decimal(value.timestamp()) - Decimal(constants.SECONDS_IN_YEAR)
    return value_as_decimal
