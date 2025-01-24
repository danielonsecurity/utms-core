from decimal import Decimal
from typing import Any, Callable, Dict
from typing import List as PyList
from typing import Literal, Optional, TypeAlias, TypedDict, Union, cast

from ..hy.types import HyExpression, HyList, HyString, HySymbol, ResolvedValue
from .protocols import CalendarUnit

OptionalHyExpression: TypeAlias = Optional[HyExpression]

PropertyValue: TypeAlias = Union[HyExpression, HySymbol, HyList, Decimal, int, str, None]
PropertyDict: TypeAlias = Dict[str, PropertyValue]


UnitType: TypeAlias = Literal["day", "week", "month", "year"]
UnitMappings: TypeAlias = Dict[UnitType, HySymbol]
UnitsDict: TypeAlias = Dict[str, CalendarUnit]
FunctionType: TypeAlias = Literal["day_of_week_fn"]

NamesList: TypeAlias = Optional[Union[HyList, PropertyValue]]


class UnitKwargs(TypedDict, total=False):
    length: PropertyValue
    timezone: PropertyValue
    start: PropertyValue
    names: NamesList
    offset: Union[int, PropertyValue]
    index: Union[int, PropertyValue]


OptionalUnitKwargs: TypeAlias = Optional[UnitKwargs]


class UnitInfo(TypedDict):
    name: str
    kwargs: UnitKwargs


class CalendarConfig(TypedDict):
    units: UnitMappings
    day_of_week: OptionalHyExpression


CalendarComponents: TypeAlias = Dict[
    Union[UnitType, FunctionType], Union[CalendarUnit, HyExpression]
]

CalendarDefinitions: TypeAlias = Dict[str, CalendarConfig]
UnitDefinitions: TypeAlias = Dict[str, UnitInfo]


ArbitraryArgs: TypeAlias = Any
ArbitraryKwargs: TypeAlias = Any


FunctionCache: TypeAlias = Dict[str, Callable[..., ResolvedValue]]


def to_unit_type(s: str) -> UnitType:
    """Convert string to UnitType with validation."""
    if s not in ("day", "week", "month", "year"):
        raise ValueError(f"Invalid unit type: {s}")
    return cast(UnitType, s)
