from typing import Any, Dict, List

import hy

from utms.core.hy.utils import format_value, is_dynamic_content
from utms.core.plugins import NodePlugin
from utms.utils import hy_to_python
from utms.utms_types import HyNode


class VariableNodePlugin(NodePlugin):
    @property
    def name(self) -> str:
        return "Variable Node Plugin"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def node_type(self) -> str:
        return "def-var"

    def initialize(self, system_context: Dict[str, Any]):
        pass

    def parse(self, expr) -> HyNode:
        """Parse variable definition."""
        if len(expr) < 3:
            return None

        var_name = str(expr[1])
        var_value = expr[2]

        # Check if the value is dynamic
        is_dynamic = is_dynamic_content(var_value)
        
        # Create a value node with dynamic information if needed
        value_node = HyNode(
            type="value",
            value=var_value,
            original=hy.repr(var_value).strip("'") if is_dynamic else None,
            is_dynamic=is_dynamic,
            field_name="value"  # Add field name to track which field this is
        )

        # Create the main variable node
        return HyNode(
            type="def-var",
            value=var_name,
            children=[value_node],
            original=hy.repr(expr),
        )

    def format(self, node: HyNode) -> List[str]:
        """Format variable definition back to Hy code."""
        if not node.children:
            return []

        # Find the value node (should be the first child)
        value_node = next((child for child in node.children if child.field_name == "value"), None)
        if not value_node:
            return []

        # Format the value based on whether it's dynamic
        if value_node.is_dynamic and value_node.original:
            value_str = value_node.original
        else:
            value_str = format_value(value_node.value)

        return [f"(def-var {node.value} {value_str})"]
