from typing import List
from ..node import HyNode
from .common import format_value

def format_pattern_to_hy(node: HyNode) -> List[str]:
    """Convert a pattern node to Hy code."""
    lines = []
    
    # Add comment if present
    if node.comment:
        lines.append(node.comment)

    lines.append(f"(def-pattern {node.value}")

    for prop in node.children:
        if prop.type == "property":
            value_node = prop.children[0]
            
            # Keep original expression for time values if available
            if value_node.original and prop.value in ["every", "at", "between", "except-between"]:
                value_str = value_node.original
            else:
                value_str = format_value(value_node.value)

            # Special handling for certain properties
            if prop.value == "at":
                # Don't wrap single values in list
                if isinstance(value_node.value, (list, tuple)) and len(value_node.value) == 1:
                    value_str = format_value(value_node.value[0])
            elif prop.value == "between" or prop.value == "except-between":
                # Format as two separate values
                if isinstance(value_node.value, (list, tuple)) and len(value_node.value) == 2:
                    value_str = f"{format_value(value_node.value[0])} {format_value(value_node.value[1])}"

            lines.append(f"  ({prop.value} {value_str})")

    lines.append(")")
    return lines
