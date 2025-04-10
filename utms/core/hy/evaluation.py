import uuid

import hy
from hy.compiler import hy_eval

from utms.core.logger import get_logger
from utms.utms_types.hy.types import (
    EvaluatedResult,
    ExpressionList,
    HyExpression,
    HySymbol,
    HyLazy,
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

    # Handle function definitions
    if isinstance(expr, HyExpression) and len(expr) > 0 and isinstance(expr[0], HySymbol):
        if str(expr[0]) == '.':
            logger.debug("Handling dot operator expression")

            # Get the object
            obj_name = str(expr[1])
            logger.debug("Object name: %s", obj_name)

            obj = locals_dict.get(obj_name)
            if obj is None:
                obj = locals_dict.get(obj_name.replace("-", "_"))
            
            logger.debug("Found object: %s", obj)
            if obj is None:
                raise NameError(f"name '{obj_name}' is not defined")

            # Get the method/attribute
            method = getattr(obj, str(expr[2]))
            logger.debug("Found method: %s", method)

            # If it's a method and there are arguments, call it
            if callable(method) and len(expr) > 3:
                args = [evaluate_hy_expression(arg, locals_dict) if isinstance(arg, (HyExpression, HySymbol)) else arg for arg in expr[3:]]
                logger.debug("Calling method with args: %s", args)
                return method(*args)
            return method

    try:
        result = hy_eval(expr, locals_dict)
        logger.debug("Evaluation result: %s", result)
        return result
    except Exception as e:
        logger.error("Evaluation error: %s", str(e))
        raise

    
