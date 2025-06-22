from collections.abc import Mapping
from decimal import Decimal
from typing import Any, Callable, Dict, Iterator
from typing import List as PyList
from typing import Literal, Optional, TypeAlias, TypedDict, TypeGuard, Union, cast

from ..base.protocols import TimeLength, TimeStamp
from ..hy.types import (
    HyExpression,
    HyInteger,
    HyList,
    HySymbol,
    NamesList,
    OptionalHyExpression,
    PropertyValue,
    ResolvedValue,
    is_list,
    is_number,
)
from .protocols import CalendarUnit

# Basic calendar literals
UnitType: TypeAlias = Literal["day", "week", "month", "year"]
FunctionType: TypeAlias = Literal["day_of_week_fn"]

# Unit related types
UnitName: TypeAlias = str
UnitIndex: TypeAlias = int
UnitLength: TypeAlias = Union[int, Decimal]

# Unit mapping types
UnitKey: TypeAlias = Union[UnitType, FunctionType]
UnitValue: TypeAlias = Union["CalendarUnit", HyExpression]
UnitKeyIterator: TypeAlias = Iterator[UnitKey]
UnitMappings: TypeAlias = Dict[UnitType, HySymbol]
UnitsDict: TypeAlias = Dict[str, "CalendarUnit"]
OptionalUnitsDict: TypeAlias = Optional[Dict[str, "CalendarUnit"]]


# Collection types
CalendarComponents: TypeAlias = Dict[UnitKey, UnitValue]
UnitAccessorMapping: TypeAlias = Mapping[UnitKey, UnitValue]
CalendarDefinitions: TypeAlias = Dict[str, "CalendarConfig"]
UnitDefinitions: TypeAlias = Dict[str, "UnitInfo"]

# Function-related types
CalendarFunction: TypeAlias = Callable[..., ResolvedValue]
FunctionCache: TypeAlias = Dict[str, CalendarFunction]


# Complex types
class UnitKwargs(TypedDict, total=False):
    length: PropertyValue
    timezone: PropertyValue
    start: PropertyValue
    names: NamesList
    offset: Union[int, PropertyValue]
    index: Union[int, PropertyValue]


OptionalUnitKwargs: TypeAlias = Optional[UnitKwargs]


class UnitInfo(TypedDict):
    name: UnitName
    kwargs: UnitKwargs


class CalendarConfig(TypedDict):
    units: UnitMappings
    day_of_week: OptionalHyExpression


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


def is_timestamp(value: Any) -> TypeGuard[Union[HyInteger, float, int, Decimal, TimeStamp]]:
    return is_number(value) or isinstance(value, TimeStamp)


def is_timelength(value: Any) -> TypeGuard[Union[HyInteger, float, int, Decimal, TimeLength]]:
    return is_number(value) or isinstance(value, TimeLength)


def is_names_list(value: Any) -> TypeGuard[Union[PyList[str], HyList]]:
    """Type guard for NamesList."""
    return is_list(value) and all(isinstance(x, str) for x in value)
