from dataclasses import dataclass
from typing import Dict, List

from utms.utils import TimeRange
from utms.utms_types import CalendarUnit


@dataclass
class YearData:
    """Data structure for year calculations."""

    year_num: int
    year_start: float
    year_length: float
    months_across: int = 3
    epoch_year: int = 1970


@dataclass
class MonthData:
    """Data structure for month-related calculations."""

    days: List[int]
    month_starts: List[float]
    month_ends: List[float]
    first_day_weekdays: List[int]


@dataclass
class CalendarState:
    """Core calendar state."""

    name: str
    timestamp: float
    week_length: int
    today_start: float
    current_week_range: TimeRange
    current_month_range: TimeRange
    units: Dict[str, CalendarUnit]
