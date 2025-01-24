from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Protocol, Union

from ..hy.types import PyList, ResolvedValue

if TYPE_CHECKING:
    from .types import FunctionCache, PropertyValue


@dataclass
class TimeRange:
    start: float
    end: float


class UnitAttributes(Protocol):
    name: str
    _values: Dict[str, "PropertyValue"]

    def get(self, prop: str) -> "ResolvedValue": ...
    def set(self, prop: str, value: "PropertyValue") -> None: ...


class CalendarUnit(Protocol):
    """Protocol defining the interface for calendar units."""

    # Required attributes
    name: str
    units: Dict[str, "CalendarUnit"]
    _attrs: UnitAttributes
    _func_cache: "FunctionCache"

    def get_value(
        self, prop: str, timestamp: Decimal = Decimal(0), *args: object, **kwargs: object
    ) -> ResolvedValue:
        """Get the value of a unit property.

        Args:
            prop: Name of the property to get
            timestamp: Optional timestamp for time-dependent properties

        Returns:
            Resolved property value
        """
        ...

    def calculate_index(self, timestamp: Decimal = Decimal(0)) -> None:
        """Calculate the index based on timestamp and unit properties.

        Args:
            timestamp: Timestamp to calculate index for
        """
        ...

    def __str__(self) -> str:
        """String representation of the unit."""
        ...

    def __repr__(self) -> str: ...


class TimeUnit(Protocol):
    """Protocol for time-based unit operations."""

    @property
    def length(self) -> "PropertyValue": ...

    @property
    def start(self) -> "PropertyValue": ...

    @property
    def timezone(self) -> "PropertyValue": ...

    def get_start(self, timestamp: float) -> float:
        """Get the start time of the unit containing the timestamp.

        Args:
            timestamp: The timestamp to get the start time for

        Returns:
            Start timestamp of the containing unit
        """
        ...

    def get_end(self, timestamp: float) -> float:
        """Get the end time of the unit containing the timestamp.

        Args:
            timestamp: The timestamp to get the end time for

        Returns:
            End timestamp of the containing unit
        """
        ...

    def get_next(self, timestamp: float) -> float:
        """Get the start time of the next unit.

        Args:
            timestamp: The reference timestamp

        Returns:
            Start timestamp of the next unit
        """
        ...

    def get_previous(self, timestamp: float) -> float:
        """Get the start time of the previous unit.

        Args:
            timestamp: The reference timestamp

        Returns:
            Start timestamp of the previous unit
        """
        ...

    def get_current(self, timestamp: float) -> float:
        """Get the normalized timestamp within the current unit.

        Args:
            timestamp: The timestamp to normalize

        Returns:
            Normalized timestamp within the current unit
        """
        ...


class NamedUnit(Protocol):
    """Protocol for units that have names (e.g., days, months)."""

    names: Optional[List[str]]
    index: int

    def get_name(self, timestamp: float = 0) -> Optional[str]:
        """Get the name of the unit for the given timestamp.

        Args:
            timestamp: Optional timestamp to determine the name

        Returns:
            The name of the unit or None if no names are defined
        """
        ...

    def get_names(self) -> Optional[List[str]]:
        """Get all possible names for this unit.

        Returns:
            List of all possible names or None if no names are defined
        """
        ...

    def get_index(self, timestamp: float = 0) -> int:
        """Get the current index in the names list.

        Args:
            timestamp: Optional timestamp to determine the index

        Returns:
            Current index in the names list
        """
        ...

    def set_index(self, index: int) -> None:
        """Set the current index in the names list.

        Args:
            index: New index value
        """
        ...


class IndexedUnit(Protocol):
    """Protocol for units that have an index (position within a cycle)."""

    index: int
    length: Decimal  # For calculating index
    start: Decimal  # Reference point for index calculation

    def get_index(self, timestamp: float = 0) -> int:
        """Get the index for the given timestamp.

        Args:
            timestamp: Timestamp to calculate index for

        Returns:
            Calculated index value
        """
        ...

    def set_index(self, index: int) -> None:
        """Set the current index.

        Args:
            index: New index value
        """
        ...

    def calculate_index(self, timestamp: float = 0) -> None:
        """Calculate and update the index based on timestamp.

        Args:
            timestamp: Timestamp to calculate index for
        """
        ...

    def get_cycle_position(self, timestamp: float = 0) -> float:
        """Get position within the current cycle (0.0 to 1.0).

        Args:
            timestamp: Timestamp to calculate position for

        Returns:
            Position within cycle as float between 0 and 1
        """
        ...

    def get_cycle_length(self, timestamp: float = 0) -> int:
        """Get the length of the complete cycle.

        Args:
            timestamp: Optional timestamp for variable cycle lengths

        Returns:
            Number of positions in the complete cycle
        """
        ...


class CalendarOperations(Protocol):
    """Protocol for calendar-wide operations."""

    name: str
    units: Dict[str, Any]  # Dictionary of calendar units

    def get_day_of_week(self, timestamp: float, timezone: Optional[float] = None) -> int:
        """Get day of week for timestamp.

        Args:
            timestamp: The timestamp to calculate for
            timezone: Optional timezone offset

        Returns:
            Day of week index (0-6)
        """
        ...

    def get_week_number(self, timestamp: float, timezone: Optional[float] = None) -> int:
        """Get week number in year.

        Args:
            timestamp: The timestamp to calculate for
            timezone: Optional timezone offset

        Returns:
            Week number (1-53)
        """
        ...

    def get_days_in_month(self, timestamp: float, timezone: Optional[float] = None) -> int:
        """Get number of days in the month.

        Args:
            timestamp: The timestamp to calculate for
            timezone: Optional timezone offset

        Returns:
            Number of days in the month
        """
        ...

    def is_leap_year(self, timestamp: float, timezone: Optional[float] = None) -> bool:
        """Check if timestamp is in a leap year.

        Args:
            timestamp: The timestamp to check
            timezone: Optional timezone offset

        Returns:
            True if leap year, False otherwise
        """
        ...

    def get_unit_by_name(self, unit_name: str) -> Optional[Any]:
        """Get a calendar unit by its name.

        Args:
            unit_name: Name of the unit to get

        Returns:
            Calendar unit if found, None otherwise
        """
        ...

    def format_timestamp(
        self, timestamp: float, format_str: str, timezone: Optional[float] = None
    ) -> str:
        """Format timestamp according to format string.

        Args:
            timestamp: The timestamp to format
            format_str: Format string (similar to strftime)
            timezone: Optional timezone offset

        Returns:
            Formatted timestamp string
        """
        ...

    def parse_date(
        self, date_str: str, format_str: Optional[str] = None, timezone: Optional[float] = None
    ) -> float:
        """Parse date string to timestamp.

        Args:
            date_str: Date string to parse
            format_str: Optional format string
            timezone: Optional timezone offset

        Returns:
            Timestamp corresponding to date string
        """
        ...


class DateFormatter(Protocol):
    """Protocol for date and time formatting operations."""

    def format(
        self,
        timestamp: float,
        format_str: str,
        timezone: Optional[float] = None,
        locale: Optional[str] = None,
    ) -> str:
        """Format timestamp according to format string.

        Args:
            timestamp: Timestamp to format
            format_str: Format string (strftime-style)
            timezone: Optional timezone offset
            locale: Optional locale name

        Returns:
            Formatted date/time string
        """
        ...

    def parse(
        self,
        date_str: str,
        format_str: Optional[str] = None,
        timezone: Optional[float] = None,
        locale: Optional[str] = None,
    ) -> float:
        """Parse date string into timestamp.

        Args:
            date_str: Date string to parse
            format_str: Optional format string
            timezone: Optional timezone offset
            locale: Optional locale name

        Returns:
            Parsed timestamp
        """
        ...

    def get_format_tokens(self) -> Dict[str, str]:
        """Get dictionary of supported format tokens.

        Returns:
            Dictionary mapping format tokens to their descriptions
        """
        ...

    def format_relative(
        self, timestamp: float, reference: Optional[float] = None, timezone: Optional[float] = None
    ) -> str:
        """Format timestamp relative to reference time.

        Args:
            timestamp: Timestamp to format
            reference: Reference timestamp (defaults to now)
            timezone: Optional timezone offset

        Returns:
            Relative time string (e.g., "2 hours ago")
        """
        ...

    def format_duration(self, seconds: float, detailed: bool = False) -> str:
        """Format duration in seconds to human-readable string.

        Args:
            seconds: Number of seconds
            detailed: Whether to include more detail

        Returns:
            Formatted duration string
        """
        ...

    def get_calendar_formats(self) -> Dict[str, str]:
        """Get dictionary of predefined calendar formats.

        Returns:
            Dictionary mapping format names to format strings
        """
        ...
