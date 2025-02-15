from typing import List
from ..node import HyNode
from .common import format_value

def format_unit_to_hy(node: HyNode) -> List[str]:
    """Convert a unit node to Hy code lines."""
    lines = []
    indent = "  "

    lines.append(f"(def-fixed-unit {node.value}")

    for prop in node.children:
        if prop.type == "property":
            value_node = prop.children[0] if prop.children else None
            if value_node:
                if value_node.is_dynamic and value_node.original:
                    value = value_node.original
                else:
                    value = format_value(value_node.value)
                lines.append(f"{indent}({prop.value} {value})")

    lines[-1] = lines[-1] + ")"
    return lines
