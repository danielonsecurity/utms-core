from typing import Any, Dict, List

import hy

from utms.core.hy.utils import format_value, is_dynamic_content
from utms.core.logger import get_logger
from utms.core.plugins import NodePlugin
from utms.utms_types import HyNode

logger = get_logger()


class FixedUnitNodePlugin(NodePlugin):
    @property
    def name(self) -> str:
        return "Fixed Unit Node Plugin"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def node_type(self) -> str:
        return "def-fixed-unit"

    def initialize(self, system_context: Dict[str, Any]):
        pass

    def parse(self, expr) -> HyNode:
        """Parse a fixed unit definition."""
        if len(expr) < 2:
            return None

        label = str(expr[1])  # The unit label
        properties = []

        # Process each property expression (starting from index 2)
        for prop in expr[2:]:
            if isinstance(prop, hy.models.Expression):
                prop_name = str(prop[0])
                prop_value = prop[1]

                is_dynamic = is_dynamic_content(prop_value)

                logger.debug(f"Property: {prop_name}")
                logger.debug(f"Value: {prop_value}")
                logger.debug(f"Is dynamic: {is_dynamic}")
                logger.debug(f"Original: {hy.repr(prop_value) if is_dynamic else None}")

                properties.append(
                    HyNode(
                        type="property",
                        value=prop_name,
                        children=[
                            HyNode(
                                type="value",
                                value=prop_value,
                                original=hy.repr(prop_value) if is_dynamic else None,
                                is_dynamic=is_dynamic,
                            )
                        ],
                    )
                )

        return HyNode(
            type="def-fixed-unit",
            value=label,
            children=properties,
            original=hy.repr(expr),
        )

    def format(self, node: HyNode) -> List[str]:
        """Format fixed unit definition back to Hy code."""
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

        # Add closing parenthesis to the last line
        if lines:
            lines[-1] = lines[-1] + ")"
        else:
            lines.append(")")

        return lines
