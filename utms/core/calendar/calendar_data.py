from dataclasses import dataclass

from utms.utms_types import (
    CalendarComponents,
    IntegerList,
    TimeLength,
    TimeRange,
    TimeStamp,
    TimeStampList,
)

from .unit_accessor import UnitAccessor


@dataclass
class YearData:
    """Data structure for year calculations."""

    year_num: int
    year_start: TimeStamp
    year_length: TimeLength
    months_across: int = 3
    epoch_year: int = 1970


@dataclass
class MonthData:
    """Data structure for month-related calculations."""

    days: IntegerList
    month_starts: TimeStampList
    month_ends: TimeStampList
    first_day_weekdays: IntegerList


@dataclass
class CalendarState:
    """Core calendar state."""

    name: str
    timestamp: TimeStamp
    week_length: int
    today_start: TimeStamp
    current_week_range: TimeRange
    current_month_range: TimeRange
    units: CalendarComponents


@dataclass
class MonthCalculationParams:
    """Parameters for month data calculation."""

    year_start: TimeStamp
    current_month: int
    months_across: int
    units: UnitAccessor
    timestamp: TimeStamp


@dataclass
class YearContext:
    """Context for year header formatting."""

    timestamp: TimeStamp
    year_length: TimeLength
    months_across: int
    week_length: int
    epoch_year: int = 1970


@dataclass
class MonthContext:
    """Context for month calculations."""

    current_timestamp: TimeStamp
    year_end: TimeStamp
    max_months: int
    month_index: int
    months_across: int
    months_added: int = 0


@dataclass
class MonthGroupData:
    """Data for collecting month group information."""

    days: IntegerList
    month_starts: TimeStampList
    month_ends: TimeStampList
    first_day_weekdays: IntegerList

    @classmethod
    def empty(cls) -> "MonthGroupData":
        """Create empty month group data."""
        return cls([], [], [], [])

    def add_month(
        self,
        current_timestamp: TimeStamp,
        month_end: TimeStamp,
        first_day_weekday: int,
    ) -> None:
        """Add data for a single month."""
        self.days.append(1)
        self.month_starts.append(current_timestamp)
        self.month_ends.append(month_end)
        self.first_day_weekdays.append(first_day_weekday)

    def to_month_data(self) -> MonthData:
        """Convert to MonthData."""
        return MonthData(self.days, self.month_starts, self.month_ends, self.first_day_weekdays)
