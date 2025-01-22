import uuid

import hy
from hy.compiler import hy_eval
from hy.models import Expression, Symbol

from utms.utils import get_logger

logger = get_logger('resolvers.hy_loader')


def evaluate_hy_file(hy_file_path):
    """Evaluates the HyLang file and returns the resulting data structures."""
    with open(hy_file_path, "r") as file:
        hy_code = file.read()
    
    logger.debug(f"Reading Hy file: {hy_file_path}")
    expressions = hy.read_many(hy_code)
    
    # Collect all expressions into a list
    expressions_list = []
    for expr in expressions:
        expressions_list.append(expr)
    
    logger.debug(f"Loaded {len(expressions_list)} expressions")
    return expressions_list


def evaluate_hy_expression(expr, locals_dict=None):
    """Generic Hy expression evaluator that can be used by both config and calendar."""
    if locals_dict is None:
        locals_dict = {}

    # Add Python builtins
    locals_dict["__builtins__"] = globals()["__builtins__"]

    # Handle function definitions
    if len(expr) > 0 and isinstance(expr[0], Symbol) and str(expr[0]) == "fn":
        func_name = f"_utms_{uuid.uuid4().hex}"
        locals_dict[func_name] = hy_eval(expr, locals_dict)
        return locals_dict[func_name]

    return hy_eval(expr, locals_dict)
