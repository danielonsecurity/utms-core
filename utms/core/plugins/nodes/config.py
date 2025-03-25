from typing import Any, Dict, List

import hy

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
        node = HyNode(type=self.node_type, value=None, original=hy.repr(expr), children=[])

        for setting in expr[1:]:
            if isinstance(setting, hy.models.Expression):
                key = str(setting[0])
                value = setting[1]
                node.children.append(
                    HyNode(
                        type="config-setting",
                        value=key,
                        children=[HyNode(type="value", value=value)],
                    )
                )

        return node

    def format(self, node: HyNode) -> List[str]:
        """Format config node to Hy code"""
        lines = ["(custom-set-config"]
        for setting in node.children:
            value_node = setting.children[0]
            lines.append(f"  ({setting.value} {hy.repr(value_node.value)})")
        lines.append(")")
        return lines
