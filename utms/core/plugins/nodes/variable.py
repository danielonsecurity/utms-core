from typing import Any, Dict, List

import hy

from utms.core.hy.utils import format_value, is_dynamic_content
from utms.core.plugins import NodePlugin
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

        is_dynamic = is_dynamic_content(var_value)

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
            original=hy.repr(expr),
        )

    def format(self, node: HyNode) -> List[str]:
        """Format variable definition back to Hy code."""
        if not node.children:
            return []

        value_node = node.children[0]
        if value_node.is_dynamic and value_node.original:
            value_str = value_node.original
        else:
            value_str = format_value(value_node.value)

        return [f"(def-var {node.value} {value_str})"]
