from typing import Any, Dict, List

import hy

from utms.core.hy.utils import format_value, is_dynamic_content
from utms.core.plugins import NodePlugin
from utms.utils import hy_to_python
from utms.utms_types import HyNode
from utms.utms_types.field.types import TypedValue, FieldType, infer_type


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
                
                # Check if there's type information (third element in the setting)
                field_type = None
                if len(setting) > 2:
                    type_str = str(setting[2])
                    field_type = FieldType.from_string(type_str)
                else:
                    field_type = infer_type(value)
                
                # Create typed value
                typed_value = TypedValue(
                    value=value,
                    field_type=field_type,
                    is_dynamic=is_dynamic,
                    original=hy.repr(value).strip("'") if is_dynamic else None
                )

                child_node = HyNode(
                    type="config-setting",
                    value=key,
                    children=[
                        HyNode(
                            type="value",
                            value=typed_value,  # Store the TypedValue here
                            original=hy.repr(value).strip("'") if is_dynamic else None,
                            is_dynamic=is_dynamic,
                            field_name="value"  # Add field name to track which field this is
                        )
                    ],
                )
                node.children.append(child_node)

        return node

    def format(self, node: HyNode) -> List[str]:
        """Format config definition back to Hy code."""
        lines = ["(custom-set-config"]

        for setting in node.children:
            # Find the value node (should be the first child)
            value_node = next((child for child in setting.children if child.field_name == "value"), None)
            if not value_node:
                continue

            # Get typed value if available
            typed_value = None
            if isinstance(value_node.value, TypedValue):
                typed_value = value_node.value
                
                # Format the value
                if typed_value.is_dynamic and typed_value.original:
                    value_str = typed_value.original
                else:
                    value_str = format_value(typed_value.value)
                    
                # Add type information if not the default inferred type
                default_type = infer_type(typed_value.value)
                if typed_value.field_type != default_type:
                    lines.append(f"  ({setting.value} {value_str} {typed_value.field_type.value})")
                else:
                    lines.append(f"  ({setting.value} {value_str})")
            else:
                # Fallback to the old approach
                if value_node.is_dynamic and value_node.original:
                    value_str = value_node.original
                else:
                    value_str = format_value(value_node.value)
                lines.append(f"  ({setting.value} {value_str})")

        lines.append(")")
        return lines


