from dataclasses import dataclass, field
from typing import List, Optional

from ..base.protocols import TimeLength, TimeRange, TimeStamp
from .repeat import RepeatPattern


@dataclass
class TimeStampSpec:
    """Specification for a timestamp with optional repeater and warning"""

    timestamp: TimeStamp
    repeater: Optional[RepeatPattern] = None
    warning_period: Optional[TimeLength] = None
    is_active: bool = True


@dataclass
class TimeRangeSpec:
    """Specification for a time range with optional repeater and warning"""

    timerange: TimeRange
    repeater: Optional[RepeatPattern] = None
    warning_period: Optional[TimeLength] = None
    is_active: bool = True


@dataclass
class ClockEntry:
    """Time tracking entry with start and end times"""

    start: TimeStamp
    end: Optional[TimeStamp] = None  # None means clock is still running


@dataclass
class CompletionRecord:
    """Record of when something was completed"""

    timestamp: TimeStamp
    count: int = 1


@dataclass
class TimeTracking:
    """Track planned vs actual times"""

    planned: TimeRangeSpec
    actual: Optional[TimeRange] = None
