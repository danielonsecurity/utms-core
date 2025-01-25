from decimal import Decimal
from typing import Any, Callable, Dict
from typing import List as PyList
from typing import Literal, Optional, TypeAlias, TypedDict, TypeGuard, Union, cast

from ..hy.types import HyExpression, HyInteger, HyList, HyString, HySymbol, ResolvedValue
from .protocols import CalendarUnit, TimeLength, Timestamp
from .timelength import DecimalTimeLength
from .timestamp import DecimalTimestamp

# Basic type aliases
TimezoneOffset: TypeAlias = Optional[Union[int, float]]
LocaleString: TypeAlias = Optional[str]
FormatString: TypeAlias = str

# Calendar-specific types
UnitType: TypeAlias = Literal["day", "week", "month", "year"]
FunctionType: TypeAlias = Literal["day_of_week_fn"]

# Hy-related types
OptionalHyExpression: TypeAlias = Optional[HyExpression]
PropertyValue: TypeAlias = Union[HyExpression, HySymbol, HyList, Decimal, int, str, None]
PropertyDict: TypeAlias = Dict[str, PropertyValue]

# Unit-related types
UnitName: TypeAlias = str
UnitIndex: TypeAlias = int
UnitLength: TypeAlias = Union[int, Decimal]
CyclePosition: TypeAlias = float
UnitMappings: TypeAlias = Dict[UnitType, HySymbol]
UnitsDict: TypeAlias = Dict[str, "CalendarUnit"]
NamesList: TypeAlias = Optional[Union[HyList, PropertyValue]]


# Function types
CalendarFunction: TypeAlias = Callable[..., ResolvedValue]
TimeCalculator: TypeAlias = Callable[[Timestamp], Timestamp]
IndexCalculator: TypeAlias = Callable[[Timestamp], int]
FormatterFunction: TypeAlias = Callable[[Timestamp, FormatString, TimezoneOffset], str]

# Cache types
FunctionCache: TypeAlias = Dict[str, CalendarFunction]
ValueCache: TypeAlias = Dict[str, Any]


# Complex types
class UnitKwargs(TypedDict, total=False):
    length: PropertyValue
    timezone: PropertyValue
    start: PropertyValue
    names: NamesList
    offset: Union[int, PropertyValue]
    index: Union[int, PropertyValue]


class UnitInfo(TypedDict):
    name: UnitName
    kwargs: UnitKwargs


class CalendarConfig(TypedDict):
    units: UnitMappings
    day_of_week: OptionalHyExpression


class TimeRange:
    """Represents a time range with start and end timestamps."""

    def __init__(self, start, end) -> None:
        self.start: Timestamp = start
        self.end: Timestamp = end

    def __post_init__(self) -> None:
        """Validate that end is not before start."""
        if self.end < self.start:
            raise ValueError("TimeRange end cannot be before start")

    @property
    def duration(self) -> Timestamp:
        """Calculate the duration of the time range."""
        return self.end - self.start

    def contains(self, timestamp: Timestamp) -> bool:
        """Check if a timestamp falls within this range."""
        return self.start <= timestamp < self.end

    def overlaps(self, other: "TimeRange") -> bool:
        """Check if this range overlaps with another range."""
        return self.start < other.end and self.end > other.start


# Args
ArbitraryArgs: TypeAlias = Any
ArbitraryKwargs: TypeAlias = Any
OptionalUnitKwargs: TypeAlias = Optional[UnitKwargs]


# Collection types
CalendarComponents: TypeAlias = Dict[
    Union[UnitType, FunctionType], Union["CalendarUnit", HyExpression]
]

CalendarDefinitions: TypeAlias = Dict[str, CalendarConfig]
UnitDefinitions: TypeAlias = Dict[str, UnitInfo]

# Result types
CalculationResult: TypeAlias = Union[int, float, Decimal, TimeRange]
FormattingResult: TypeAlias = str


# Error types
class CalendarError(Exception):
    pass


class UnitError(CalendarError):
    pass


class CalculationError(CalendarError):
    pass


class FormattingError(CalendarError):
    pass


# Validation functions
def to_unit_type(s: str) -> UnitType:
    """Convert string to UnitType with validation."""
    if s not in ("day", "week", "month", "year"):
        raise ValueError(f"Invalid unit type: {s}")
    return cast(UnitType, s)


def is_timestamp(obj: Any) -> TypeGuard[Union[HyInteger, float, int, Decimal, Timestamp]]:
    return isinstance(obj, (HyInteger, float, int, Decimal, DecimalTimestamp))


def is_timelength(obj: Any) -> TypeGuard[Union[HyInteger, float, int, Decimal, TimeLength]]:
    return isinstance(obj, (HyInteger, float, int, DecimalTimeLength))
