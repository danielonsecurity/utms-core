from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Protocol

from ..base.protocols import TimeLength, TimeStamp
from ..base.types import ArbitraryKwargs
from ..hy.types import ResolvedValue

if TYPE_CHECKING:
    from .types import FunctionCache, NamesList, PropertyDict, PropertyValue


class UnitAttributes(Protocol):
    name: str
    _values: Dict[str, "PropertyValue"]

    def get(self, prop: str) -> "ResolvedValue": ...
    def set(self, prop: str, value: "PropertyValue") -> None: ...
    def get_all(self) -> "PropertyDict": ...

    # String conversion
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...


class CalendarUnit(Protocol):
    """Protocol defining the interface for calendar units."""

    # Required attributes
    name: str
    units: Dict[str, "CalendarUnit"]
    _attrs: UnitAttributes
    _func_cache: "FunctionCache"

    def get_value(
        self, prop: str, timestamp: TimeStamp = None, *args: object, **kwargs: object
    ) -> ResolvedValue: ...

    def get_start(self, timestamp: TimeStamp = None, **kwargs: "ArbitraryKwargs") -> TimeStamp: ...

    def get_length(
        self, timestamp: TimeStamp = None, **kwargs: "ArbitraryKwargs"
    ) -> TimeLength: ...

    def get_timezone(
        self, timestamp: TimeStamp = None, **kwargs: "ArbitraryKwargs"
    ) -> TimeLength: ...

    def get_names(
        self, timestamp: TimeStamp = None, **kwargs: "ArbitraryKwargs"
    ) -> "NamesList": ...

    def get_offset(self, timestamp: TimeStamp = None, **kwargs: "ArbitraryKwargs") -> Decimal: ...

    def get_index(self, timestamp: TimeStamp = None, **kwargs: "ArbitraryKwargs") -> int: ...

    def get_property(self, prop: str) -> "PropertyValue": ...
    def set_property(self, prop: str, value: "PropertyValue") -> None: ...
    def get_all_properties(self) -> "PropertyDict": ...

    def calculate_index(self, timestamp: TimeStamp = None) -> None: ...

    def __str__(self) -> str: ...

    def __repr__(self) -> str: ...


class TimeUnit(Protocol):
    """Protocol for time-based unit operations."""

    @property
    def length(self) -> "PropertyValue": ...

    @property
    def start(self) -> "PropertyValue": ...

    @property
    def timezone(self) -> "PropertyValue": ...

    def get_start(self, timestamp: float) -> float: ...

    def get_end(self, timestamp: float) -> float: ...

    def get_next(self, timestamp: float) -> float: ...

    def get_previous(self, timestamp: float) -> float: ...

    def get_current(self, timestamp: float) -> float: ...


class NamedUnit(Protocol):
    """Protocol for units that have names (e.g., days, months)."""

    names: Optional[List[str]]
    index: int

    def get_name(self, timestamp: float = 0) -> Optional[str]: ...

    def get_names(self) -> Optional[List[str]]: ...

    def get_index(self, timestamp: float = 0) -> int: ...

    def set_index(self, index: int) -> None: ...


class IndexedUnit(Protocol):
    """Protocol for units that have an index (position within a cycle)."""

    index: int
    length: Decimal  # For calculating index
    start: Decimal  # Reference point for index calculation

    def get_index(self, timestamp: float = 0) -> int: ...

    def set_index(self, index: int) -> None: ...

    def calculate_index(self, timestamp: float = 0) -> None: ...

    def get_cycle_position(self, timestamp: float = 0) -> float: ...

    def get_cycle_length(self, timestamp: float = 0) -> int: ...


class CalendarOperations(Protocol):
    """Protocol for calendar-wide operations."""

    name: str
    units: Dict[str, Any]  # Dictionary of calendar units

    def get_day_of_week(self, timestamp: float, timezone: Optional[float] = None) -> int: ...

    def get_week_number(self, timestamp: float, timezone: Optional[float] = None) -> int: ...

    def get_days_in_month(self, timestamp: float, timezone: Optional[float] = None) -> int: ...

    def is_leap_year(self, timestamp: float, timezone: Optional[float] = None) -> bool: ...

    def get_unit_by_name(self, unit_name: str) -> Optional[Any]: ...

    def format_timestamp(
        self, timestamp: float, format_str: str, timezone: Optional[float] = None
    ) -> str: ...

    def parse_date(
        self, date_str: str, format_str: Optional[str] = None, timezone: Optional[float] = None
    ) -> float: ...


class DateFormatter(Protocol):
    """Protocol for date and time formatting operations."""

    def format(
        self,
        timestamp: float,
        format_str: str,
        timezone: Optional[float] = None,
        locale: Optional[str] = None,
    ) -> str: ...

    def parse(
        self,
        date_str: str,
        format_str: Optional[str] = None,
        timezone: Optional[float] = None,
        locale: Optional[str] = None,
    ) -> float: ...

    def get_format_tokens(self) -> Dict[str, str]: ...

    def format_relative(
        self, timestamp: float, reference: Optional[float] = None, timezone: Optional[float] = None
    ) -> str: ...

    def format_duration(self, seconds: float, detailed: bool = False) -> str: ...

    def get_calendar_formats(self) -> Dict[str, str]: ...
