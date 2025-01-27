from typing import Any, Dict, Optional, Protocol, Union

from .types import (
    Context,
    EvaluatedResult,
    ExpressionList,
    HyExpression,
    HySymbol,
    HyValue,
    LocalsDict,
    ResolvedValue,
)


class ExpressionResolver(Protocol):
    """Protocol for objects that can resolve Hy expressions."""

    def resolve(
        self,
        expr: HyValue,
        context: Optional[Context] = None,
        local_names: Optional[LocalsDict] = None,
    ) -> ResolvedValue: ...


class PropertyResolver(Protocol):
    """Protocol for objects that can resolve unit properties."""

    def resolve_unit_property(
        self,
        value: Any,
        units: Dict[str, Any],  # This could be more specific with CalendarUnit type
        current_unit: Any,
        timestamp: Optional[float] = None,
    ) -> ResolvedValue: ...

    def resolve(
        self,
        expr: Any,
        context: Any,
        local_names: Optional[Dict[str, Any]] = None,
    ) -> ResolvedValue: ...


class LocalsProvider(Protocol):
    """Protocol for objects that provide local variable contexts."""

    def get_locals_dict(
        self, context: Optional[Context], local_names: Optional[LocalsDict] = None
    ) -> LocalsDict: ...


class HyEvaluator(Protocol):
    """Protocol for Hy expression evaluation."""

    def evaluate(
        self,
        expr: Union[HyExpression, HySymbol, str],
        locals_dict: Optional[Dict[str, Any]] = None,
        filename: Optional[str] = None,
    ) -> Any: ...

    def evaluate_function(
        self, expr: HyExpression, globals_dict: Optional[Dict[str, Any]] = None
    ) -> EvaluatedResult: ...

    def create_function(
        self, func: ResolvedValue, globals_dict: Dict[str, Any]
    ) -> EvaluatedResult: ...

    def compile_expression(
        self, expr: Union[HyExpression, HySymbol, str], filename: Optional[str] = None
    ) -> Any: ...

    def is_function_definition(self, expr: HyExpression) -> bool: ...


class HyLoader(Protocol):
    """Protocol for loading and processing Hy code."""

    def load_file(
        self, file_path: str, locals_dict: Optional[Dict[str, Any]] = None
    ) -> ExpressionList: ...

    def load_string(
        self,
        source: str,
        locals_dict: Optional[Dict[str, Any]] = None,
        filename: Optional[str] = None,
    ) -> ExpressionList: ...

    def load_expression(
        self, expr: HyExpression, locals_dict: Optional[Dict[str, Any]] = None
    ) -> Any: ...

    def reload_file(
        self, file_path: str, locals_dict: Optional[Dict[str, Any]] = None
    ) -> ExpressionList: ...

    def get_cached_expressions(
        self,
        file_path: str,
    ) -> ExpressionList: ...

    def clear_cache(self) -> None:
        """Clear all cached expressions."""
        ...
