import uuid

import hy
from hy.compiler import hy_eval

from utms.core.logger import get_logger

from utms.utms_types.hy.types import EvaluatedResult, ExpressionList, HyExpression, HyLazy, LocalsDict, is_symbol


logger = get_logger("core.hy.evaluation")


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

    # Handle function definitions
    if len(expr) > 0:
        first_element = expr[0]
        if is_symbol(first_element) and str(first_element) == "fn":
            func_name: str = f"_utms_{uuid.uuid4().hex}"
            locals_dict[func_name] = hy_eval(expr, locals_dict)
            return locals_dict[func_name]

    return hy_eval(expr, locals_dict)
