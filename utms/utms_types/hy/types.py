from decimal import Decimal
from typing import Any, Callable, Dict
from typing import List as PyList
from typing import Optional, TypeAlias, TypeGuard, Union

from hy.models import Expression, Integer, Lazy, List, String, Symbol

HyExpression: TypeAlias = Expression
HySymbol: TypeAlias = Symbol
HyList: TypeAlias = List
HyInteger: TypeAlias = Integer
HyString: TypeAlias = String
HyCompound: TypeAlias = Union[Expression, Symbol, List]
HyLazy: TypeAlias = Lazy
HyValue: TypeAlias = Union[
    Integer,
    float,
    int,
    Decimal,
    String,
    Symbol,
    List,
    Expression,
]


ResolvedValue: TypeAlias = Union[
    int,
    float,
    Decimal,
    str,
    PyList[Any],
    Callable[..., Any],
    Any,
]

Context: TypeAlias = Optional[Any]


ExpressionList: TypeAlias = PyList[HyExpression]

LocalsDict: TypeAlias = Optional[Dict[str, Any]]
EvaluatedResult: TypeAlias = Union[Callable[..., Any], Any]

OptionalHyExpression: TypeAlias = Optional[HyExpression]

PropertyValue: TypeAlias = Union[HyExpression, HySymbol, HyList, Decimal, int, str, None]
PropertyDict: TypeAlias = Dict[str, PropertyValue]
NamesList: TypeAlias = Optional[Union[HyList, PyList[str]]]


def is_symbol(obj: Any) -> TypeGuard[Symbol]:
    return isinstance(obj, Symbol)


def is_number(obj: Any) -> TypeGuard[Union[Integer, float, int, Decimal]]:
    return isinstance(obj, (Integer, float, int, Decimal))


def is_string(obj: Any) -> TypeGuard[String]:
    return isinstance(obj, (str, String))


def is_list(obj: Any) -> TypeGuard[List]:
    return isinstance(obj, (List, PyList))


def is_expression(obj: Any) -> TypeGuard[Expression]:
    return isinstance(obj, Expression)


def is_hy_compound(obj: Any) -> TypeGuard[HyCompound]:
    return isinstance(obj, Expression)
