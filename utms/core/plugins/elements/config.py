from typing import Any, Dict, List

import hy

from utms.core.hy.utils import format_value, is_dynamic_content
from utms.core.plugins import NodePlugin
from utms.utils import hy_to_python
from utms.utms_types import HyNode
from utms.utms_types.field.types import FieldType, TypedValue, infer_type


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
                    original=hy.repr(value).strip("'") if is_dynamic else None,
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
                            field_name="value",  # Add field name to track which field this is
                        )
                    ],
                )
                node.children.append(child_node)

        return node

    def format(self, node: HyNode) -> List[str]:
        """Format config definition back to Hy code."""
        lines = ["(custom-set-config"]

        for setting in node.children:
            value_node = next(
                (child for child in setting.children if child.field_name == "value"), None
            )
            if not value_node:
                continue
            key = setting.value
            if isinstance(value_node.value, TypedValue):
                typed_value = value_node.value
                value_str = typed_value.serialize_for_persistence()
                add_type_hint = False
                if typed_value.field_type not in [FieldType.STRING] and not typed_value.is_dynamic:
                    try:
                        inferred_type = infer_type(typed_value.value)
                    except Exception:
                        inferred_type = FieldType.STRING
                    if typed_value.field_type != inferred_type:
                        add_type_hint = True
                if add_type_hint:
                    lines.append(f"  ({key} {value_str} {typed_value.field_type.value})")
                else:
                    lines.append(f"  ({key} {value_str})")
            else:
                fallback_value_str = hy.repr(value_node.value)
                lines.append(f"  ({key} {fallback_value_str})")

        lines.append(")")
        return lines
