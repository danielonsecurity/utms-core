from typing import Any, Dict, List

import hy

from utms.core.hy.utils import hy_obj_to_string, is_dynamic_content
from utms.core.logger import get_logger
from utms.core.plugins import NodePlugin
from utms.utms_types import HyNode

logger = get_logger()


class AnchorNodePlugin(NodePlugin):
    @property
    def name(self) -> str:
        return "Anchor Node Plugin"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def node_type(self) -> str:
        return "def-anchor"

    def initialize(self, system_context: Dict[str, Any]):
        pass

    def parse(self, expr) -> HyNode:
        """Parse an anchor definition."""
        if len(expr) < 2:
            return None

        name = str(expr[1])  # The anchor name/label
        properties = []

        # Process each property expression (starting from index 2)
        for prop in expr[2:]:
            if isinstance(prop, hy.models.Expression):
                prop_name = str(prop[0])
                prop_value = prop[1]

                # For dynamic expressions (like function calls or complex expressions)
                is_dynamic = is_dynamic_content(prop_value)

                logger.debug(f"Property: {prop_name}")
                logger.debug(f"Value: {prop_value}")
                logger.debug(f"Is dynamic: {is_dynamic}")
                original = str(prop_value) if is_dynamic else None
                logger.debug(f"Original: {original}")

                properties.append(
                    HyNode(
                        type="property",
                        value=prop_name,
                        children=[
                            HyNode(
                                type="value",
                                value=prop_value,
                                original=original,
                                is_dynamic=is_dynamic,
                            )
                        ],
                    )
                )

        return HyNode(
            type="def-anchor",
            value=name,
            children=properties,
            original=hy.repr(expr),
        )

    def format(self, node: HyNode) -> List[str]:
        """Format anchor definition back to Hy code."""
        lines = [f"(def-anchor {node.value}"]

        for prop in node.children:
            if prop.type == "property":
                value_node = prop.children[0]
                if value_node.is_dynamic and value_node.original:
                    value_str = value_node.original
                else:
                    value_str = hy_obj_to_string(value_node.value)

                lines.append(f"  ({prop.value} {value_str})")

        lines.append(")")
        return lines
