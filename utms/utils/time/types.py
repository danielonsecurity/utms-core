from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


@dataclass
class TimeRange:
    start: float
    end: float


class CalendarUnitProtocol(Protocol):
    """Protocol defining the interface needed by time utilities."""

    offset: float

    def get_value(self, prop: str, timestamp: float = 0) -> float: ...
