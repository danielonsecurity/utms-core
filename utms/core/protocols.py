from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol, Dict, Any, List, Optional, Union


@dataclass
class TimeRange:
    start: float
    end: float


class CalendarUnitProtocol(Protocol):
    """Protocol defining the interface needed by time utilities."""
    name: str
    units: Dict[str, Any]
    length: Decimal
    start: Decimal
    names: Optional[List[str]]
    timezone: Decimal
    offset: int
    index: int

    def get_value(self, prop: str, timestamp: float = 0) -> Union[float, str, List[str], None]:
        ...
