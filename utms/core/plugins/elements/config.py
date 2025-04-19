from typing import Any, Dict, List

import hy

from utms.core.hy.utils import format_value, is_dynamic_content
from utms.core.plugins import NodePlugin
from utms.utils import hy_to_python
from utms.utms_types import HyNode


class ConfigNodePlugin(NodePlugin):
    @property
    def name(self) -> str:
        return "Config Node Plugin"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def node_type(self) -> str:
        return "custom-set-config"

    def initialize(self, system_context: Dict[str, Any]):
        pass

    def parse(self, expr) -> HyNode:
        """Parse a custom-set-config expression"""
        node = HyNode(
            type=self.node_type, value=None, original=hy.repr(expr).strip("'"), children=[]
        )

        # Skip the first element (custom-set-config)
        for setting in expr[1:]:
            if isinstance(setting, (list, hy.models.List, hy.models.Expression)):
                key = str(setting[0])
                value = setting[1]
                is_dynamic = is_dynamic_content(value)

                child_node = HyNode(
                    type="config-setting",
                    value=key,
                    children=[
                        HyNode(
                            type="value",
                            value=value,
                            original=hy.repr(value).strip("'") if is_dynamic else None,
                            is_dynamic=is_dynamic,
                        )
                    ],
                )
                node.children.append(child_node)

        return node

    def format(self, node: HyNode) -> List[str]:
        """Format config definition back to Hy code."""
        lines = ["(custom-set-config"]

        for setting in node.children:
            value_node = setting.children[0]

            # Use original expression for dynamic values
            if value_node.is_dynamic and value_node.original:
                value_str = value_node.original
            else:
                value_str = format_value(value_node.value)

            lines.append(f"  ({setting.value} {value_str})")

        lines.append(")")
        return lines
