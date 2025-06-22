from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

from utms.core.time import DecimalTimeStamp
from utms.utms_types import TimeRange, TimeStamp
from utms.utms_types.calendar.protocols import CalendarUnit as CalendarUnitProtocol


def get_timezone(unit, timestamp=None):
    timezone_offset_seconds = unit.get_value("timezone", timestamp)

    return timezone(timedelta(seconds=float(timezone_offset_seconds)))


def get_day_of_week(
    timestamp: TimeStamp, week_unit: CalendarUnitProtocol, day_unit: CalendarUnitProtocol
) -> int:
    """Calculate day of week using pure arithmetic.

    Args:
        timestamp: Seconds since epoch
        week_unit: The week unit definition
        day_unit: The day unit definition

    Returns:
        Integer representing the day of week (0-based index)
    """
    decimal_timestamp = DecimalTimeStamp(timestamp)
    day_length = day_unit.get_length(decimal_timestamp)
    week_length = week_unit.get_length(decimal_timestamp)
    week_offset = week_unit.get_offset()  # Get timezone offset in seconds
    timezone_offset = day_unit.get_timezone(decimal_timestamp)

    # Calculate the reference point (1970-01-01 00:00:00)
    epoch_reference = 0  # Unix epoch starts at 0

    # Apply week offset and timezone offset to reference point
    reference = epoch_reference + (week_offset * day_length) - timezone_offset

    # Calculate days elapsed from reference, adjusting for timezone
    days_elapsed = (decimal_timestamp - reference) // day_length

    # Calculate day of week
    days_per_week = week_length // day_length
    day_of_week = int(days_elapsed % days_per_week)

    return day_of_week


def get_time_range(timestamp: TimeStamp, unit: CalendarUnitProtocol) -> TimeRange:
    start = unit.get_start(timestamp)
    end = start + unit.get_length(timestamp)
    return TimeRange(start, end)
