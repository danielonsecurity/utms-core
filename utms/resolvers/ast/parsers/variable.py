import hy
from utms.utils import get_logger
from ..node import HyNode
from ..utils import is_dynamic_content

logger = get_logger("resolvers.ast.parsers.variable")

def parse_variable_def(expr: hy.models.Expression, original: str) -> HyNode:
    """Parse a def-var expression."""
    if len(expr) < 3:
        return None

    var_name = str(expr[1])
    var_value = expr[2]
    
    is_dynamic = is_dynamic_content(var_value)

    logger.debug(f"Variable: {var_name}")
    logger.debug(f"Value: {var_value}")
    logger.debug(f"Is dynamic: {is_dynamic}")
    logger.debug(f"Original: {hy.repr(var_value) if is_dynamic else None}")

    return HyNode(
        type="def-var",
        value=var_name,
        children=[
            HyNode(
                type="value",
                value=var_value,
                original=hy.repr(var_value) if is_dynamic else None,
                is_dynamic=is_dynamic,
            )
        ],
        original=original
    )
