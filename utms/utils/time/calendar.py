from datetime import datetime, timedelta, timezone

from .types import CalendarUnitProtocol, TimeRange


def get_timezone(unit, timestamp=None):
    timezone_offset_seconds = unit.get_value("timezone", timestamp)

    return timezone(timedelta(seconds=float(timezone_offset_seconds)))


def get_day_of_week(
    timestamp: float, week_unit: CalendarUnitProtocol, day_unit: CalendarUnitProtocol
) -> int:
    tz = get_timezone(day_unit, timestamp)
    reference_datetime = datetime(1970, 1, 1, tzinfo=tz) + timedelta(days=week_unit.offset)
    reference_timestamp = reference_datetime.timestamp()

    total_days_elapsed = (timestamp - reference_timestamp) // day_unit.get_value(
        "length", timestamp
    )
    day_of_week = int(
        total_days_elapsed
        % (week_unit.get_value("length", timestamp) // day_unit.get_value("length", timestamp))
    )

    return day_of_week


def get_time_range(timestamp: float, unit: CalendarUnitProtocol) -> TimeRange:
    start = unit.get_value("start", timestamp)
    end = start + unit.get_value("length", timestamp)
    return TimeRange(start, end)
