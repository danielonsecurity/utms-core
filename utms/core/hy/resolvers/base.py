import time
from datetime import datetime, timedelta
from types import FunctionType, ModuleType
from typing import Any, Set, Tuple, TYPE_CHECKING

import hy
from hy.compiler import hy_eval

from utms.core.hy import evaluate_hy_expression
from utms.core.hy.utils import is_dynamic_content
from utms.core.mixins import ResolverMixin
from utms.core.hy.converter import converter

if TYPE_CHECKING:
    from utms.utms_types import (
        Context,
        DynamicExpressionInfo,
        ExpressionResolver,
        HyDict,
        HyExpression,
        HyKeyword,
        HyList,
        HySymbol,
        HyValue,
        LocalsDict,
        LocalsProvider,
        ResolvedValue,
    )

KNOWN_HY_CORE_SYMBOLS: Set[str] = {
    "+",
    "-",
    "*",
    "/",
    "%",
    "//",
    "and",
    "or",
    "not",
    "if",
    "cond",
    "when",
    "unless",
    "let",
    "setv",
    "fn",
    "defn",
    "defmacro",
    "quote",
    "quasiquote",
    "unquote",
    "unquote-splice",
    "do",
    "progn",
    "get",
}


class HyResolver(ResolverMixin):
    def __init__(self) -> None:
        self.default_globals = {
            "datetime": datetime,
            "timedelta": timedelta,
            "time": time,
        }

    def get_additional_globals(self):
        return {}

    def resolve(
        self, expr: "HyValue", context: "Context" = None, local_names: "LocalsDict" = None
    ) -> Tuple[Any, "DynamicExpressionInfo"]:
        """
        Main resolution method that handles both static and dynamic expressions

        Returns:
            Tuple[resolved_value, dynamic_info]
        """
        from utms.utms_types import DynamicExpressionInfo
        # Create dynamic expression info first
        dynamic_info = DynamicExpressionInfo(original=expr, is_dynamic=is_dynamic_content(expr))
        self.logger.debug(
            f"HyResolver.resolve: expr='{expr}', type(expr)='{type(expr)}', is_dynamic='{dynamic_info.is_dynamic}'"
        )

        try:
            resolved_value = self._resolve_value(expr, context, local_names)
            dynamic_info.add_evaluation(
                resolved_value,
                original_expr=expr,
                metadata={
                    "context_type": str(type(context).__name__) if context else None,
                    "local_names_keys": list(local_names.keys()) if local_names else None,
                },
            )
            self.logger.debug(f"HyResolver.resolve: SUCCESS, resolved_value='{resolved_value}'")
            return resolved_value, dynamic_info
        except Exception as e:
            self.logger.error(f"HyResolver.resolve: FAILED for expr='{expr}': {e}", exc_info=True)
            dynamic_info.add_evaluation(
                None,
                original_expr=expr,
                metadata={"error_type": type(e).__name__, "error_message": str(e)},
            )
            raise

    def _resolve_value(
        self, expr: "HyValue", context: "Context" = None, local_names: "LocalsDict" = None
    ) -> "ResolvedValue":
        from utms.utms_types import HySymbol, HyExpression, HyList, HyDict, HyKeyword
        self.logger.debug(f"HyResolver._resolve_value: expr='{expr}' (type: {type(expr)})")

        if isinstance(expr, hy.models.String):
            return str(expr)
        elif isinstance(expr, hy.models.Integer):
            return int(expr)
        elif isinstance(expr, hy.models.Float):
            return float(expr)
        elif isinstance(expr, hy.models.Bytes):
            return bytes(expr)
        elif isinstance(expr, hy.models.Keyword):
            return str(expr)[1:] if str(expr).startswith(':') else str(expr)
        elif isinstance(expr, hy.models.Symbol):
            return self._resolve_symbol(expr, context, local_names)

        if isinstance(expr, (str, int, float, bool, type(None), datetime, bytes, bytearray)):
            return expr

        if isinstance(expr, HyExpression):
            return self._resolve_expression(expr, context, local_names)
        elif isinstance(expr, HyList):
            return [self._resolve_value(item, context, local_names) for item in expr]
        elif isinstance(expr, HyDict):
            py_dict = {}
            it = iter(expr)
            try:
                while True:
                    k_expr = next(it)
                    v_expr = next(it)
                    resolved_k = self._resolve_value(k_expr, context, local_names)
                    resolved_v = self._resolve_value(v_expr, context, local_names)
                    py_dict[resolved_k] = resolved_v
            except StopIteration:
                pass
            return py_dict
        elif isinstance(expr, HyKeyword):
            return str(expr)[1:]

        self.logger.debug(
            f"HyResolver._resolve_value: Unhandled type {type(expr)}, returning as is: {expr}"
        )
        return expr

    def get_locals_dict(
        self, component_context: "Context", local_scope_names: "LocalsDict" = None
    ) -> "LocalsDict":
        """
        Constructs the full dictionary of names available for an evaluation.
        `component_context`: 'self' or other component-specific objects.
        `local_scope_names`: Variables defined in the current scope (e.g., from let bindings or previous defs).
        """
        full_locals = {**self.default_globals}
        full_locals.update(self.get_additional_globals() or {})

        if isinstance(component_context, dict):
            full_locals.update(component_context)
        elif component_context is not None:
            full_locals["self"] = component_context

        if local_scope_names:
            full_locals.update(local_scope_names)

        self.logger.debug(f"HyResolver.get_locals_dict: final keys: {list(full_locals.keys())}")
        return full_locals

    def _resolve_symbol(
        self, sym: "HySymbol", context: "Context", local_names: "LocalsDict"
    ) -> "ResolvedValue":
        """
        Resolves a HySymbol.
        If the symbol's value in local_names is another HyExpression or HySymbol,
        it's recursively resolved.
        """
        from utms.utms_types import HyExpression, HySymbol, HyList, HyDict
        symbol_name = str(sym)
        self.logger.debug(f"HyResolver._resolve_symbol: '{symbol_name}'")
        if symbol_name == "True":
            return True
        if symbol_name == "False":
            return False
        if symbol_name == "None":
            return None

        evaluation_scope = self.get_locals_dict(context, local_names)

        value_from_scope: Any = None
        found_in_scope = False

        if symbol_name in evaluation_scope:
            value_from_scope = evaluation_scope[symbol_name]
            found_in_scope = True
        elif symbol_name.replace("-", "_") in evaluation_scope:  # Check for Pythonic name
            value_from_scope = evaluation_scope[symbol_name.replace("-", "_")]
            found_in_scope = True

        if found_in_scope:
            self.logger.debug(
                f"HyResolver._resolve_symbol: '{symbol_name}' found in scope, value_type: {type(value_from_scope)}, value: {value_from_scope}"
            )
            if isinstance(value_from_scope, (HyExpression, HySymbol, HyList, HyDict)):
                self.logger.debug(
                    f"HyResolver._resolve_symbol: '{symbol_name}' resolved to another Hy object, recursing _resolve_value."
                )
                return self._resolve_value(value_from_scope, context, local_names)
            else:
                return value_from_scope
        else:
            if symbol_name in KNOWN_HY_CORE_SYMBOLS:
                self.logger.debug(
                    f"HyResolver._resolve_symbol: '{symbol_name}' is a known Hy core symbol, returning as HySymbol for hy_eval."
                )
                return sym
            self.logger.warning(
                f"HyResolver._resolve_symbol: '{symbol_name}' not found in current scope and not a known Hy core symbol. Returning as HySymbol."
            )

            return sym

    def _resolve_argument_to_native(
        self, arg_expr: Any, context: "Context", current_scope_locals: "LocalsDict"
    ) -> Any:
        """
        Helper to fully resolve an argument expression to its Python native value.
        `current_scope_locals` is the dictionary of names for the *current* expression's evaluation.
        """
        self.logger.debug(f"HyResolver._resolve_argument_to_native: arg_expr='{arg_expr}'")
        resolved_arg = self._resolve_value(arg_expr, context, current_scope_locals)
        final_py_arg = converter.model_to_py(resolved_arg, raw=True)
        self.logger.debug(
            f"HyResolver._resolve_argument_to_native: resolved_arg='{resolved_arg}', final_py_arg='{final_py_arg}' (type: {type(final_py_arg)})"
        )
        return final_py_arg

    def _resolve_expression(
        self, expr: "HyExpression", context: "Context", local_names: "LocalsDict"
    ) -> "ResolvedValue":
        """
        Resolves a HyExpression. Handles dot operator, function calls.
        `local_names` are the variables/bindings available in the scope of `expr`.
        """
        from utms.utms_types import HySymbol, HyKeyword
        self.logger.debug(
            f"HyResolver._resolve_expression: expr='{expr}', local_names_keys: {list(local_names.keys()) if local_names else 'None'}"
        )
        if len(expr) == 1 and isinstance(expr[0], HySymbol):
            self.logger.debug(
                f"Resolving single-symbol expression {expr} as a direct symbol lookup."
            )
            resolved_symbol_value = self._resolve_symbol(expr[0], context, local_names)
            if callable(resolved_symbol_value):
                self.logger.debug(
                    f"Resolved single-symbol expression to a callable function '{resolved_symbol_value.__name__}'. Calling it."
                )
                return resolved_symbol_value()
            else:
                return resolved_symbol_value
        if not expr:  # Empty expression like '()'
            self.logger.debug(
                "HyResolver._resolve_expression: Empty expression, returning empty list."
            )
            return []
        current_scope_locals = self.get_locals_dict(context, local_names)

        first_element_expr = expr[0]

        if isinstance(first_element_expr, HySymbol) and str(first_element_expr) == ".":
            if len(expr) < 3:
                raise ValueError(f"Invalid dot operator expression: {expr}")

            obj_expr_to_resolve = expr[1]
            resolved_obj_intermediate = self._resolve_value(
                obj_expr_to_resolve, context, local_names
            )
            py_obj = converter.model_to_py(
                resolved_obj_intermediate,
                raw=True
            )  

            prop_name = str(
                expr[2]
            )
            if (
                isinstance(py_obj, dict)
                and isinstance(obj_expr_to_resolve, HySymbol)
                and str(obj_expr_to_resolve) == "self"
            ):
                if prop_name in py_obj:
                    method_or_attr = py_obj[prop_name]
                else:
                    prop_name_underscore = prop_name.replace("-", "_")
                    if prop_name_underscore in py_obj:
                        method_or_attr = py_obj[prop_name_underscore]
                    else:
                        self.logger.error(
                            f"AttributeError on self (dict): Key '{prop_name}' or '{prop_name_underscore}' not found in self context {py_obj}"
                        )
                        raise AttributeError(f"Key '{prop_name}' not found in self context.")
            else:
                try:
                    method_or_attr = getattr(py_obj, prop_name)
                except AttributeError:
                    self.logger.error(
                        f"AttributeError in dot-op: '{prop_name}' not found on object {py_obj} (from expr: {obj_expr_to_resolve})"
                    )
                    raise

            if callable(method_or_attr):
                if len(expr) > 3:
                    raw_method_args_exprs = expr[3:]
                    python_method_args = [
                        self._resolve_argument_to_native(arg_e, context, current_scope_locals)
                        for arg_e in raw_method_args_exprs
                    ]
                    self.logger.debug(
                        f"HyResolver: Calling dot-op method: {prop_name} on {py_obj} with args: {python_method_args}"
                    )
                    return method_or_attr(*python_method_args)
                else:  
                    self.logger.debug(
                        f"HyResolver: Calling dot-op method: {prop_name} on {py_obj} (no args)"
                    )
                    return method_or_attr()
            else:  
                self.logger.debug(
                    f"HyResolver: Accessing dot-op attribute: {prop_name} on {py_obj}"
                )
                return method_or_attr
        callable_candidate = self._resolve_value(first_element_expr, context, local_names)

        py_callable = converter.model_to_py(callable_candidate, raw=True)

        if callable(py_callable):
            python_pos_args = []
            python_kw_args = {}

            arg_exprs_iter = expr[1:] 
            idx = 0
            while idx < len(arg_exprs_iter):
                current_arg_expr = arg_exprs_iter[idx]
                if isinstance(current_arg_expr, HyKeyword):
                    if idx + 1 < len(arg_exprs_iter):
                        key_name = str(current_arg_expr)[1:] 
                        val_expr = arg_exprs_iter[idx + 1]
                        python_kw_args[key_name] = self._resolve_argument_to_native(
                            val_expr, context, current_scope_locals
                        )
                        idx += 1
                    else:
                        raise ValueError(
                            f"Keyword argument {current_arg_expr} is missing a value in expression: {expr}"
                        )
                else: 
                    python_pos_args.append(
                        self._resolve_argument_to_native(
                            current_arg_expr, context, current_scope_locals
                        )
                    )
                idx += 1

            self.logger.debug(
                f"HyResolver: Calling Python function '{py_callable.__name__ if hasattr(py_callable, '__name__') else py_callable}' with pos_args: {python_pos_args}, kw_args: {python_kw_args}"
            )
            try:
                return py_callable(*python_pos_args, **python_kw_args)
            except TypeError as te:
                self.logger.error(
                    f"TypeError calling function '{str(py_callable)}': {te}. Args: {python_pos_args}, Kwargs: {python_kw_args}. Original expr: {expr}",
                    exc_info=True,
                )
                raise
        else:
            is_known_hy_symbol_head = (
                isinstance(callable_candidate, HySymbol)
                and str(callable_candidate) in KNOWN_HY_CORE_SYMBOLS
            )
            if not is_known_hy_symbol_head:

                self.logger.warning(
                    f"HyResolver: Head of expression '{first_element_expr}' (resolved to '{callable_candidate}') is not callable "
                    f"and not a known Hy core symbol. Falling back to 'hylang_eval' for: {expr}"
                )
            else:
                self.logger.debug(
                    f"HyResolver: Head of expression '{first_element_expr}' is known Hy core symbol '{callable_candidate}'. "
                    f"Falling back to 'hylang_eval' for: {expr}"
                )

            try:
                return evaluate_hy_expression(expr, current_scope_locals)
            except Exception as e_fallback:
                self.logger.error(
                    f"Fallback 'evaluate_hy_expression' failed for {expr}: {e_fallback}",
                    exc_info=True,
                )
                raise

    def _resolve_list(
        self, expr: "HyList", context: "Context", local_names: "LocalsDict" = None
    ) -> "ResolvedValue":
        from utms.utms_types import is_hy_compound
        return [
            (self._resolve_value(item, context, local_names) if is_hy_compound(item) else item)
            for item in expr
        ]
