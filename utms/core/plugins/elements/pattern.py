from typing import Any, Dict, List

import hy

from utms.core.hy.utils import hy_obj_to_string, is_dynamic_content
from utms.core.logger import get_logger
from utms.core.plugins import NodePlugin
from utms.utms_types import HyNode

logger = get_logger()


class PatternNodePlugin(NodePlugin):
    @property
    def name(self) -> str:
        return "Pattern Node Plugin"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def node_type(self) -> str:
        return "def-pattern"

    def initialize(self, system_context: Dict[str, Any]):
        pass

    def parse(self, expr) -> HyNode:
        """Parse a pattern definition."""
        if len(expr) < 2:
            return None

        name = str(expr[1])
        properties = []

        for prop in expr[2:]:
            if isinstance(prop, hy.models.Expression):
                prop_name = str(prop[0])

                # Handle properties that should be pairs
                if prop_name in ["between", "except-between"]:
                    if len(prop) != 3:  # Should have name and two values
                        logger.warning(f"Expected two values for {prop_name}, got {len(prop)-1}")
                        continue
                    # Create a list of the two values
                    prop_value = hy.models.List([prop[1], prop[2]])
                else:
                    prop_value = prop[1]

                is_dynamic = is_dynamic_content(prop_value)
                properties.append(
                    HyNode(
                        type="property",
                        value=prop_name,
                        children=[
                            HyNode(
                                type="value",
                                value=prop_value,
                                original=hy.repr(prop_value).strip("'") if is_dynamic else None,
                                is_dynamic=is_dynamic,
                            )
                        ],
                    )
                )

        return HyNode(
            type="def-pattern",
            value=name,
            children=properties,
            original=hy.repr(expr),
        )

    def format(self, node: HyNode) -> List[str]:
        """Format pattern definition back to Hy code."""
        lines = []

        # Add comment if present
        if node.comment:
            lines.append(node.comment)

        lines.append(f"(def-pattern {node.value}")

        for prop in node.children:
            if prop.type == "property":
                value_node = prop.children[0]

                # Keep original expression for time values if available
                if value_node.original and prop.value in [
                    "every",
                    "at",
                    "between",
                    "except-between",
                ]:
                    value_str = value_node.original
                else:
                    value_str = hy_obj_to_string(value_node.value)

                # Special handling for certain properties
                if prop.value == "at":
                    # Don't wrap single values in list
                    if isinstance(value_node.value, (list, tuple)) and len(value_node.value) == 1:
                        value_str = hy_obj_to_string(value_node.value[0])
                elif prop.value in ["between", "except-between"]:
                    # Format as two separate values
                    if isinstance(value_node.value, (list, tuple)) and len(value_node.value) == 2:
                        value_str = f"{hy_obj_to_string(value_node.value[0])} {format_value(value_node.value[1])}"

                lines.append(f"  ({prop.value} {value_str})")

        lines.append(")")
        return lines
