import datetime
import time
from types import FunctionType, ModuleType  # pylint: disable=no-name-in-module

from utms.core.logger import get_logger
from utms.utms_types import (
    Context,
    EvaluatedResult,
    ExpressionList,
    ExpressionResolver,
    HyExpression,
    HyKeyword,
    HyList,
    HySymbol,
    HyValue,
    LocalsDict,
    LocalsProvider,
    ResolvedValue,
    is_expression,
    is_hy_compound,
    is_list,
    is_number,
    is_string,
    is_symbol,
)
from utms.core.hy import evaluate_hy_expression

logger = get_logger()


class HyResolver(ExpressionResolver, LocalsProvider):
    def __init__(self) -> None:
        self.default_globals = {
            "datetime": datetime,
            "time": time,
        }

    def get_additional_globals(self):
        return {}

    def resolve(
        self, expr: HyValue, context: Context = None, local_names: LocalsDict = None
    ) -> ResolvedValue:
        """Main resolution method"""
        logger.debug("Resolving expression: %s", expr)
        logger.debug("context: %s", context)
        logger.debug("local_names: %s", local_names)
        result = None
        # or if you want to catch it in any form:
        if is_symbol(expr):
            symbol_name = str(expr)
            if local_names and symbol_name in local_names:
                result = local_names[symbol_name]
            elif local_names and symbol_name.replace("-", "_") in local_names:
                result = local_names[symbol_name.replace("-", "_")]

        elif is_number(expr):
            result = expr
        elif is_string(expr):
            result = str(expr)
        elif is_list(expr):
            result = self._resolve_list(expr, context, local_names)
        elif is_expression(expr):
            result = self._resolve_expression(expr, context, local_names)
        else:
            result = expr
        logger.debug("Resolved expression: %s", result)

        return result

    def get_locals_dict(
        self, context: Context, local_names: LocalsDict = None  # pylint: disable=W0613
    ) -> LocalsDict:
        """Override this in subclasses to provide context-specific locals"""
        return local_names or {}

    def _resolve_symbol(
        self, expr: HySymbol, _: Context, local_names: LocalsDict = None
    ) -> ResolvedValue:
        """Base symbol resolution - override in subclasses if needed"""
        symbol_name = str(expr)
        # Try with hyphen
        if local_names and symbol_name in local_names:
            return local_names[symbol_name]
        # Try with underscore
        underscore_name = symbol_name.replace("-", "_")
        if local_names and underscore_name in local_names:
            return local_names[underscore_name]
        return expr

        # if local_names and str(expr) in local_names:
        #     return local_names[str(expr)]
        # return expr

    def _resolve_list(
        self, expr: HyList, context: Context, local_names: LocalsDict = None
    ) -> ResolvedValue:
        return [
            (self.resolve(item, context, local_names) if is_hy_compound(item) else item)
            for item in expr
        ]

    def _resolve_expression(
        self, expr: HyExpression, context: Context, local_names: LocalsDict = None
    ) -> ResolvedValue:
        """Main resolution method"""
        if local_names is None:
            local_names = {}

        self._log_initial_state(expr, context, local_names)

        resolved_subexprs = []
        for subexpr in expr:
            if is_symbol(subexpr):
                symbol_name = str(subexpr)
                if symbol_name in local_names:
                    resolved_subexprs.append(local_names[symbol_name])
                elif symbol_name.replace("-", "_") in local_names:
                    resolved_subexprs.append(local_names[symbol_name.replace("-", "_")])
                else:
                    resolved_subexprs.append(subexpr)
            elif isinstance(subexpr, HyExpression):
                resolved_value = self.resolve(subexpr, context, local_names)
                resolved_subexprs.append(resolved_value)
            else:
                resolved_subexprs.append(subexpr)

        locals_dict = self.get_locals_dict(context, local_names)
        logger.debug("Final locals dictionary: %s", locals_dict)

        try:
            return self._evaluate_with_dot_operator(expr, resolved_subexprs, locals_dict)
        except NameError as e:
            logger.debug("NameError: %s, returning unresolved expression", e)
            return HyExpression(resolved_subexprs)
        except Exception as e:
            logger.error("Error evaluating expression: %s", expr)
            logger.error("Error detali[s: %s: %s", type(e).__name__, e)
            raise e

    def _log_initial_state(
        self, expr: HyExpression, context: Context, local_names: LocalsDict
    ) -> None:
        """Log the initial state of expression resolution."""
        logger.debug("\nResolving expression: %s", expr)
        logger.debug("Expression type: %s", type(expr))
        logger.debug("Context: %s", context)
        logger.debug("Local names: %s", local_names)

    def _resolve_subexpressions(
        self, expr: HyExpression, context: Context, local_names: LocalsDict
    ) -> ExpressionList:
        """Resolve all subexpressions in the given expression."""
        resolved_subexprs: ExpressionList = []
        for subexpr in expr:
            if is_expression(subexpr):
                logger.debug("Resolving subexpression: %s", subexpr)
                resolved = self.resolve(subexpr, context, local_names)
                logger.debug("Resolved to: %s", resolved)
                resolved_subexprs.append(subexpr if callable(resolved) else resolved)
            else:
                resolved_subexprs.append(subexpr)
                logger.debug("Added literal: %s", subexpr)
        return resolved_subexprs

    def _is_dot_operator(self, expr: HyExpression) -> bool:
        """Check if expression is a dot operator expression."""
        return is_expression(expr) and len(expr) > 2 and str(expr[0]) == "."

    def _evaluate_with_dot_operator(
        self,
        expr: HyExpression,
        resolved_subexprs: ExpressionList,
        locals_dict: LocalsDict,
    ) -> ResolvedValue:
        """Evaluate expression, handling dot operator if present."""
        if self._is_dot_operator(expr):
            obj = self._resolve_dot_operator_object(expr[1], locals_dict)
            method = self._resolve_dot_operator_property(obj, str(expr[2]))

            # If there are additional arguments, call the method with them
            if len(expr) > 3:
                args = [self.resolve(arg, None, locals_dict) for arg in expr[3:]]
                return method(*args)
            return method

        # If first element is a type/class, call it directly with the resolved arguments
        if isinstance(resolved_subexprs[0], type):
            constructor = resolved_subexprs[0]
            # Separate args and kwargs
            args = []
            kwargs = {}
            for arg in resolved_subexprs[1:]:
                if isinstance(arg, HyKeyword):
                    # Remove the leading ':' from keyword name
                    key = str(arg)[1:]
                    # Next value is the keyword's value
                    value = next(iter(resolved_subexprs[resolved_subexprs.index(arg) + 1 :]), None)
                    kwargs[key] = (
                        locals_dict.get(str(value), value) if isinstance(value, HySymbol) else value
                    )
                elif not isinstance(arg, HyKeyword) and arg not in kwargs.values():
                    # Only add to args if it's not a keyword and not already used as a kwarg value
                    args.append(
                        locals_dict.get(str(arg), arg) if isinstance(arg, HySymbol) else arg
                    )

            return constructor(*args, **kwargs)

        result = evaluate_hy_expression(HyExpression(resolved_subexprs), locals_dict)
        logger.debug("Final result: %s", result)
        return result

    def _resolve_dot_operator_object(
        self,
        obj_expr: HyExpression,
        locals_dict: LocalsDict,
    ) -> EvaluatedResult:
        """Resolve the object part of a dot operator expression."""
        logger.debug("Object expression: %s", obj_expr)

        if is_symbol(obj_expr):
            obj_name = str(obj_expr)
            logger.debug("Looking up symbol: %s in locals", obj_name)
            if locals_dict and obj_name in locals_dict:
                obj = locals_dict[obj_name]
                logger.debug("Found object: %s", obj)
                return obj
            elif obj_name.replace("-", "_") in locals_dict:
                obj = locals_dict[obj_name.replace("-", "_")]
                logger.debug("Found object with underscore: %s", obj)
                return obj
            logger.debug("Symbol not found in locals")
            raise NameError(f"name '{obj_name}' is not defined")

        try:
            obj = evaluate_hy_expression(HyExpression([obj_expr]), locals_dict)
            logger.debug("Evaluated object: %s", obj)
            return obj
        except Exception as e:
            logger.error("Error evaluating object expression %s", e)

    def _resolve_dot_operator_property(
        self,
        obj: HyExpression,
        prop: str,
    ) -> EvaluatedResult:
        """Resolve property access in dot operator expression."""
        logger.debug("Accessing property: %s", prop)
        value = getattr(obj, prop)
        logger.debug("Got value: %s", value)
        if isinstance(value, (type, ModuleType)):
            return value

        if callable(value) and hasattr(value, "__globals__"):
            return self._create_bound_function(obj, value)
        return value

    def _create_bound_function(
        self,
        obj: HyExpression,
        value: EvaluatedResult,
    ) -> EvaluatedResult:
        """Create a bound function with the appropriate globals."""

        func_globals = {
            **value.__globals__,
            "self": obj,
            **self.default_globals,
            **self.get_additional_globals(),
            **(obj.units if hasattr(obj, "units") else {}),
        }
        logger.debug("Creating function with globals: %s", list(func_globals.keys()))

        return FunctionType(
            value.__code__,
            func_globals,
            value.__name__,
            value.__defaults__,
            value.__closure__,
        )
