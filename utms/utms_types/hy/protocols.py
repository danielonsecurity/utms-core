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
    ) -> ResolvedValue:
        """Resolve a Hy expression to its final value.

        Args:
            expr: The Hy expression to resolve
            context: Optional context for resolution
            local_names: Optional dictionary of local names

        Returns:
            The resolved value
        """
        ...


class PropertyResolver(Protocol):
    """Protocol for objects that can resolve unit properties."""

    def resolve_unit_property(
        self,
        value: Any,
        units: Dict[str, Any],  # This could be more specific with CalendarUnit type
        current_unit: Any,
        timestamp: Optional[float] = None,
    ) -> ResolvedValue:
        """Resolve a unit property to its final value.

        Args:
            value: The property value to resolve
            units: Dictionary of available units
            current_unit: The unit containing the property
            timestamp: Optional timestamp for time-dependent properties

        Returns:
            The resolved property value
        """
        ...

    def resolve(
        self,
        expr: Any,
        context: Any,
        local_names: Optional[Dict[str, Any]] = None,
    ) -> ResolvedValue:
        """Resolve any expression in the property context.

        Args:
            expr: The expression to resolve
            context: The resolution context
            local_names: Optional dictionary of local names

        Returns:
            The resolved value
        """
        ...


class LocalsProvider(Protocol):
    """Protocol for objects that provide local variable contexts."""

    def get_locals_dict(
        self, context: Optional[Context], local_names: Optional[LocalsDict] = None
    ) -> LocalsDict:
        """Get dictionary of local variables for expression evaluation.

        Args:
            context: Optional context object (e.g., calendar unit)
            local_names: Optional initial dictionary of local names

        Returns:
            Dictionary containing all local variables for expression evaluation
        """
        ...


class HyEvaluator(Protocol):
    """Protocol for Hy expression evaluation."""

    def evaluate(
        self,
        expr: Union[HyExpression, HySymbol, str],
        locals_dict: Optional[Dict[str, Any]] = None,
        filename: Optional[str] = None,
    ) -> Any:
        """Evaluate a Hy expression.

        Args:
            expr: Hy expression to evaluate
            locals_dict: Optional dictionary of local variables
            filename: Optional filename for error reporting

        Returns:
            Result of evaluation
        """
        ...

    def evaluate_function(
        self, expr: HyExpression, globals_dict: Optional[Dict[str, Any]] = None
    ) -> EvaluatedResult:
        """Evaluate a Hy function definition.

        Args:
            expr: Hy function expression
            globals_dict: Optional dictionary of global variables

        Returns:
            Compiled function object
        """
        ...

    def create_function(self, func: ResolvedValue, globals_dict: Dict[str, Any]) -> EvaluatedResult:
        """Create a new function with modified globals.

        Args:
            func: Original function
            globals_dict: New globals dictionary

        Returns:
            New function with updated globals
        """
        ...

    def compile_expression(
        self, expr: Union[HyExpression, HySymbol, str], filename: Optional[str] = None
    ) -> Any:
        """Compile a Hy expression without evaluating.

        Args:
            expr: Hy expression to compile
            filename: Optional filename for error reporting

        Returns:
            Compiled code object
        """
        ...

    def is_function_definition(self, expr: HyExpression) -> bool:
        """Check if expression is a function definition.

        Args:
            expr: Expression to check

        Returns:
            True if expression is a function definition
        """
        ...


class HyLoader(Protocol):
    """Protocol for loading and processing Hy code."""

    def load_file(
        self, file_path: str, locals_dict: Optional[Dict[str, Any]] = None
    ) -> ExpressionList:
        """Load and parse Hy code from a file.

        Args:
            file_path: Path to the Hy source file
            locals_dict: Optional dictionary of local variables

        Returns:
            List of parsed Hy expressions

        Raises:
            FileNotFoundError: If file doesn't exist
            SyntaxError: If Hy code is invalid
        """
        ...

    def load_string(
        self,
        source: str,
        locals_dict: Optional[Dict[str, Any]] = None,
        filename: Optional[str] = None,
    ) -> ExpressionList:
        """Load and parse Hy code from a string.

        Args:
            source: Hy source code string
            locals_dict: Optional dictionary of local variables
            filename: Optional filename for error reporting

        Returns:
            List of parsed Hy expressions

        Raises:
            SyntaxError: If Hy code is invalid
        """
        ...

    def load_expression(
        self, expr: HyExpression, locals_dict: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Load and evaluate a single Hy expression.

        Args:
            expr: Hy expression (string or Expression object)
            locals_dict: Optional dictionary of local variables

        Returns:
            Result of expression evaluation
        """
        ...

    def reload_file(
        self, file_path: str, locals_dict: Optional[Dict[str, Any]] = None
    ) -> ExpressionList:
        """Reload a Hy file, clearing any cached data.

        Args:
            file_path: Path to the Hy source file
            locals_dict: Optional dictionary of local variables

        Returns:
            List of parsed Hy expressions
        """
        ...

    def get_cached_expressions(
        self,
        file_path: str,
    ) -> ExpressionList:
        """Get cached expressions for a file if available.

        Args:
            file_path: Path to the Hy source file

        Returns:
            Cached expressions or None if not cached
        """
        ...

    def clear_cache(self) -> None:
        """Clear all cached expressions."""
        ...
