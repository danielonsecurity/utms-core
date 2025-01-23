from decimal import Decimal
from typing import Union, Dict, Any, Callable, Optional, TypeAlias, List as PyList, TypeGuard
from hy.models import Expression, Symbol, Lazy, Integer, String, List


HyExpression: TypeAlias = Expression
HySymbol: TypeAlias = Symbol
HyList: TypeAlias = List
HyInteger: TypeAlias = Integer
HyString: TypeAlias = String
HyCompound = Union[Expression, Symbol, List]
HyLazy: TypeAlias = Lazy
HyValue = Union[
    Integer,
    float,
    int,
    Decimal,
    String,
    Symbol,
    List,
    Expression,
]


ResolvedValue = Union[
    int,
    float,
    Decimal,
    str,
    PyList[Any],
    Callable[..., Any],
    Any,
]

Context = Optional[Any] # TODO


ExpressionList = PyList[HyExpression]

LocalsDict = Optional[Dict[str, Any]]
EvaluatedResult = Union[Callable[..., Any], Any]




def is_symbol(obj: Any) -> TypeGuard[Symbol]:
    return isinstance(obj, Symbol)

def is_number(obj: Any) -> TypeGuard[Union[Integer, float, int, Decimal]]:
    return isinstance(obj, (Integer, float, int, Decimal))

def is_string(obj: Any) -> TypeGuard[String]:
    return isinstance(obj, String)

def is_list(obj: Any) -> TypeGuard[List]:
    return isinstance(obj, List)

def is_expression(obj: Any) -> TypeGuard[Expression]:
    return isinstance(obj, Expression)

def is_hy_compound(obj: Any) -> TypeGuard[HyCompound]:
    return isinstance(obj, Expression)
