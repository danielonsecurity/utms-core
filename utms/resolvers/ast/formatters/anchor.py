from typing import List

from ..node import HyNode
from .common import format_value


def format_anchor_to_hy(node: HyNode) -> List[str]:
    """Convert an anchor node to Hy code."""
    lines = [f"(def-anchor {node.value}"]

    for prop in node.children:
        if prop.type == "property":
            value_node = prop.children[0]
            if value_node.is_dynamic and value_node.original:
                value_str = value_node.original
            else:
                value_str = format_value(value_node.value)

            lines.append(f"  ({prop.value} {value_str})")

    lines.append(")")
    return lines
