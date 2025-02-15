from typing import List
from ..node import HyNode
from .common import format_value

def format_variable_to_hy(node: HyNode) -> List[str]:
    """Convert a variable node to Hy code."""
    if not node.children:
        return []

    value_node = node.children[0]
    if value_node.is_dynamic and value_node.original:
        value_str = value_node.original
    else:
        value_str = format_value(value_node.value)

    return [f"(def-var {node.value} {value_str})"]
