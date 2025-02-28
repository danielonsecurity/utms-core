from datetime import datetime, timezone
from decimal import Decimal
from typing import Union

from utms.core.config import constants


def calculate_decimal_time(seconds: int) -> tuple[int, int, int, float]:
    """Calculate deciday, centiday, decimal seconds, and decidays as a
    float."""
    deciday = seconds // 8640
    centiday = (seconds % 8640) // 864
    decimal_seconds = int(seconds - centiday * 864 - deciday * 8640)
    decidays_float = seconds / 8640
    return deciday, centiday, decimal_seconds, decidays_float


def calculate_standard_time(seconds: int) -> str:
    """Calculate standard time in HH:MM:SS format."""
    total_minutes = seconds // 60
    hours = (total_minutes // 60) % 24
    minutes = total_minutes % 60
    standard_seconds = seconds - hours * 3600 - minutes * 60
    return f"{hours:02}:{minutes:02}:{standard_seconds:02}"


def convert_time(input_time: str) -> str:
    """Converts time between 24-hour format (HH:MM:SS or HH:MM) and decimal
    format (DD.CD.SSS or DD.CD).

    Args:
        input_time (str): The input time in either 24-hour format or decimal format.

    Returns:
        str: The converted time in the opposite format.
    """
    # Check if the input is in 24-hour format (HH:MM:SS or HH:MM)
    if ":" in input_time:
        return convert_to_decimal(input_time)

    # Check if the input is in decimal format (DD.CD.SSS or DD.CD)
    if "." in input_time:
        return convert_to_24h(input_time)

    raise ValueError("Invalid time format. Use HH:MM:SS, HH:MM, DD.CD.SSS, or DD.CD.")


def convert_to_decimal(time_24h: str) -> str:
    """Converts 24-hour format (HH:MM:SS or HH:MM) to decimal format (DD.CD.SSS
    or DD.CD).

    Args:
        time_24h (str): The time in 24-hour format (HH:MM:SS or HH:MM).

    Returns:
        str: The time in decimal format (DD.CD.SSS or DD.CD).
    """
    # Extract hours, minutes, and optional seconds
    time_parts = time_24h.split(":")
    hours = int(time_parts[0])
    minutes = int(time_parts[1])
    seconds = int(time_parts[2]) if len(time_parts) > 2 else 0

    # Total seconds since midnight
    total_seconds = hours * 3600 + minutes * 60 + seconds

    # Convert to decimal time
    decidays = total_seconds // 8640  # 1 deciday = 8640 seconds
    remaining_seconds = total_seconds % 8640
    centidays = remaining_seconds // 864  # 1 centiday = 864 seconds
    decimal_seconds = (remaining_seconds % 864) / 864  # The fractional part of decimal seconds

    # Format the decimal time to have one digit for centiday and optional milliseconds
    decimal_time = f"{decidays}.{centidays}.{int(decimal_seconds * 864):03}"

    return decimal_time


def convert_to_24h(decimal_time: str) -> str:
    """Converts decimal format (DD.CD.SSS or DD.CD) to 24-hour format (HH:MM:SS
    or HH:MM).

    Args:
        decimal_time (str): The time in decimal format (DD.CD.SSS or DD.CD).

    Returns:
        str: The time in 24-hour format (HH:MM:SS or HH:MM).
    """
    # Split decimal time into deciday and centiday (and optional centisecond)
    time_parts = decimal_time.split(".")
    decidays = int(time_parts[0])
    centidays = int(time_parts[1])
    decimal_seconds = int(time_parts[2]) if len(time_parts) > 2 else 0

    # Calculate total seconds
    total_seconds = (decidays * 8640) + (centidays * 864) + decimal_seconds

    # Convert total seconds to hours, minutes, and seconds
    hours = total_seconds // 3600
    total_seconds %= 3600
    minutes = total_seconds // 60
    seconds = total_seconds % 60

    return f"{hours:02}:{minutes:02}:{seconds:02}"


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
