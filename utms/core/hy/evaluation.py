import uuid

import hy
from hy.compiler import hy_eval

from utms.core.logger import get_logger
from utms.utms_types.hy.types import (
    EvaluatedResult,
    ExpressionList,
    HyExpression,
    HyLazy,
    HySymbol,
    LocalsDict,
    is_symbol,
)

logger = get_logger()


def evaluate_hy_file(hy_file_path: str) -> ExpressionList:
    """Evaluates the HyLang file and returns the resulting data structures."""
    with open(hy_file_path, "r", encoding="utf-8") as file:
        hy_code: str = file.read()

    logger.debug("Reading Hy file: %s", hy_file_path)
    expressions: HyLazy = hy.read_many(hy_code)

    # Collect all expressions into a list
    expressions_list: ExpressionList = []
    for expr in expressions:
        expressions_list.append(expr)

    logger.debug("Loaded %d expressions", len(expressions_list))
    return expressions_list


def evaluate_hy_expression(expr: HyExpression, locals_dict: LocalsDict = None) -> EvaluatedResult:
    """Generic Hy expression evaluator that can be used by both config and calendar."""
    if locals_dict is None:
        locals_dict = {}

    # Add Python builtins
    locals_dict["__builtins__"] = globals()["__builtins__"]
    logger.debug("Expression to evaluate: %s", expr)
    logger.debug("Expression type: %s", type(expr))

    if isinstance(expr, HyExpression) and len(expr) > 0 and isinstance(expr[0], HySymbol):
        if str(expr[0]) == ".":
            # Direct dot operator expression
            return handle_dot_operator(expr, locals_dict)

    try:
        result = hy_eval(expr, locals_dict)
        logger.debug("Evaluation result: %s", result)
        return result
    except Exception as e:
        if "parse error for pattern macro '.'" in str(e):
            return handle_expression_with_dot(expr, locals_dict)
        logger.error("Evaluation error: %s", str(e))
        raise


def handle_dot_operator(expr, locals_dict):
    """Handle dot operator expressions manually."""
    if len(expr) < 3:
        raise ValueError("Invalid dot operator expression")

    # Get the object
    obj_name = str(expr[1])
    obj = locals_dict.get(obj_name)
    if obj is None:
        obj = locals_dict.get(obj_name.replace("-", "_"))

    if obj is None:
        raise NameError(f"name '{obj_name}' is not defined")

    # Get the method/attribute
    method_name = str(expr[2])
    method = getattr(obj, method_name)

    # If it's a method and there are arguments, call it
    if callable(method) and len(expr) > 3:
        args = []
        for arg in expr[3:]:
            if isinstance(arg, hy.models.String):
                args.append(str(arg))
            elif isinstance(arg, (hy.models.Expression, hy.models.Symbol)):
                try:
                    args.append(evaluate_hy_expression(arg, locals_dict))
                except Exception:
                    args.append(arg)
            else:
                args.append(arg)
        return method(*args)
    return method


def handle_expression_with_dot(expr, locals_dict):
    """Handle expressions that contain dot operator subexpressions."""
    # This is a recursive function to find and handle dot operators within an expression
    if isinstance(expr, hy.models.Expression):
        # If this is a dot operator, handle it directly
        if len(expr) > 0 and isinstance(expr[0], hy.models.Symbol) and str(expr[0]) == ".":
            return handle_dot_operator(expr, locals_dict)

        # Otherwise, process each element and rebuild the expression
        processed_elements = []
        for element in expr:
            if isinstance(element, hy.models.Expression):
                processed_elements.append(handle_expression_with_dot(element, locals_dict))
            else:
                processed_elements.append(element)

        # Try to evaluate the processed expression
        try:
            return hy_eval(hy.models.Expression(processed_elements), locals_dict)
        except Exception as e:
            logger.error(f"Error evaluating processed expression: {e}")
            # If we still can't evaluate it, return the processed elements
            return processed_elements

    return expr
