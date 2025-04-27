import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Callable
from typing import Dict
from typing import Dict as PyDict
from typing import List
from typing import List as PyList
from typing import Optional, TypeAlias, TypeGuard, Union

from hy.models import Dict, Expression, Integer, Keyword, Lazy, List, String, Symbol


HyExpression: TypeAlias = Expression
HySymbol: TypeAlias = Symbol
HyKeyword: TypeAlias = Keyword
HyList: TypeAlias = List
HyDict: TypeAlias = Dict
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


@dataclass
class HyProperty:
    """Represents a property that can have both evaluated and original form."""

    value: Any
    is_dynamic: bool
    original: Optional[Any] = None


@dataclass
class HyNode:
    """A node in the Hy AST."""

    type: str  # 'def-anchor', 'def-event', 'property', 'value', 'comment'
    value: Any  # The actual value/content
    children: Optional[List["HyNode"]] = None
    comment: Optional[str] = None  # Associated comment if any
    original: Optional[str] = None  # Original Hy expression
    is_dynamic: bool = False
    field_name: Optional[str] = None  # Added field to track which field this node represents

    def __post_init__(self):
        self.children = self.children or []

ExpressionList: TypeAlias = PyList[HyExpression]

LocalsDict: TypeAlias = Optional[Dict[str, Any]]
EvaluatedResult: TypeAlias = Union[Callable[..., Any], Any]

OptionalHyExpression: TypeAlias = Optional[HyExpression]

PropertyValue: TypeAlias = Union[HyExpression, HySymbol, HyList, Decimal, int, str, None]
PropertyDict: TypeAlias = Dict[str, PropertyValue]
NamesList: TypeAlias = Optional[Union[HyList, PyList[str]]]


@dataclass
class EvaluationRecord:
    """
    Represents a single evaluation of a dynamic expression

    Attributes:
        value: The resolved value of the expression
        timestamp: When the evaluation occurred
        original_expr: The expression used for this specific evaluation
        record_id: Unique identifier for the record
        metadata: Additional context or metadata about the evaluation
    """

    value: Any
    timestamp: datetime = field(default_factory=datetime.now)
    original_expr: Optional[Any] = None
    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: dict = field(default_factory=dict)


@dataclass
class DynamicExpressionInfo:
    """
    Comprehensive tracking of a dynamic expression's lifecycle

    Attributes:
        original: The original, base dynamic expression
        is_dynamic: Whether the expression is considered dynamic
        history: List of evaluation records
        created_at: When the dynamic expression was first tracked
        last_evaluated: Timestamp of the most recent evaluation
        evaluation_count: Number of times the expression has been evaluated
    """

    original: Any
    is_dynamic: bool = True
    history: List[EvaluationRecord] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def last_evaluated(self) -> Optional[datetime]:
        """Get the timestamp of the most recent evaluation"""
        return self.history[-1].timestamp if self.history else None

    @property
    def evaluation_count(self) -> int:
        """Get the total number of evaluations"""
        return len(self.history)

    @property
    def latest_value(self) -> Optional[Any]:
        """Get the most recently evaluated value"""
        return self.history[-1].value if self.history else None

    def add_evaluation(
        self, value: Any, original_expr: Optional[Any] = None, metadata: Optional[dict] = None
    ) -> EvaluationRecord:
        """
        Add a new evaluation to the expression's history

        Args:
            value: The resolved value
            original_expr: Optional specific expression used for this evaluation
            metadata: Optional additional context for the evaluation

        Returns:
            The created EvaluationRecord
        """
        record = EvaluationRecord(
            value=value, original_expr=original_expr or self.original, metadata=metadata or {}
        )
        self.history.append(record)
        return record

    def get_evaluations_since(self, timestamp: datetime) -> List[EvaluationRecord]:
        """
        Retrieve evaluations that occurred after a specific timestamp

        Args:
            timestamp: The cutoff time

        Returns:
            List of evaluation records after the given timestamp
        """
        return [record for record in self.history if record.timestamp > timestamp]

    def __repr__(self):
        return (
            f"DynamicExpressionInfo("
            f"original={self.original}, "
            f"is_dynamic={self.is_dynamic}, "
            f"evaluations={len(self.history)}, "
            f"last_evaluated={self.last_evaluated})"
        )

    def to_dict(self) -> dict:
        """
        Convert the DynamicExpressionInfo to a dictionary representation

        Useful for serialization and API responses
        """
        return {
            "original": str(self.original),
            "is_dynamic": self.is_dynamic,
            "created_at": self.created_at.isoformat(),
            "last_evaluated": self.last_evaluated.isoformat() if self.last_evaluated else None,
            "evaluation_count": self.evaluation_count,
            "latest_value": self.latest_value,
            "history": [
                {
                    "record_id": record.record_id,
                    "value": record.value,
                    "timestamp": record.timestamp.isoformat(),
                    "original_expr": str(record.original_expr),
                    "metadata": record.metadata,
                }
                for record in self.history
            ],
        }


def is_symbol(obj: Any) -> TypeGuard[Symbol]:
    return isinstance(obj, Symbol)


def is_number(obj: Any) -> TypeGuard[Union[Integer, float, int, Decimal]]:
    return isinstance(obj, (Integer, float, int, Decimal))


def is_string(obj: Any) -> TypeGuard[String]:
    return isinstance(obj, (str, String))


def is_list(obj: Any) -> TypeGuard[List]:
    return isinstance(obj, (List, PyList))


def is_dict(obj: Any) -> TypeGuard[Dict]:
    return isinstance(obj, (Dict, PyDict))


def is_expression(obj: Any) -> TypeGuard[Expression]:
    return isinstance(obj, Expression)


def is_hy_compound(obj: Any) -> TypeGuard[HyCompound]:
    return isinstance(obj, Expression)
