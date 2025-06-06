from typing import Any, Dict, List, Optional

import hy
from hy.models import Expression, Symbol

from utms.core.hy.utils import format_value, is_dynamic_content
from utms.core.plugins import NodePlugin
from utms.utils import hy_to_python
from utms.utms_types import HyNode
from utms.utms_types.field.types import FieldType, TypedValue, infer_type


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

    def parse(self, expr: hy.models.Expression) -> HyNode:
        """
        Parse variable definition (e.g., (def-var my-var (+ 1 2))).
        It now creates a TypedValue for the variable's value.
        """
        if len(expr) < 3:
            self.logger.warning(f"Invalid def-var expression (too short): {expr}")
            return None

        var_name = str(expr[1])
        raw_hy_value_object = expr[2]  # This is the raw Hy object or literal

        self.logger.debug(f"Parsing variable: '{var_name}' with raw value: {raw_hy_value_object}")

        # Determine if the value is dynamic
        is_dynamic = is_dynamic_content(raw_hy_value_object)
        original_expr_str: Optional[str] = None

        if is_dynamic or isinstance(raw_hy_value_object, (Expression, Symbol)):
            original_expr_str = hy.repr(raw_hy_value_object)
        elif raw_hy_value_object is not None:
            original_expr_str = hy.repr(raw_hy_value_object)

        # Infer FieldType or specify if schema allowed it (not for variables, so infer)
        field_type_enum = infer_type(raw_hy_value_object)

        typed_value_for_variable = TypedValue(
            value=raw_hy_value_object,  # Store the raw Hy expression/object
            field_type=field_type_enum,
            is_dynamic=is_dynamic,
            original=original_expr_str,
        )
        node_value_data = {"name": var_name, "typed_value_for_var_value": typed_value_for_variable}

        node = HyNode(
            type=self.node_type,
            value=node_value_data,
            children=[],
            original=hy.repr(expr),
        )
        self.logger.debug(
            f"Created HyNode for variable '{var_name}' with TypedValue: {repr(typed_value_for_variable)}"
        )
        return node

    def format(self, node: HyNode) -> List[str]:
        """Format variable definition back to Hy code."""
        node_value_data: Optional[Dict[str, Any]] = node.value
        if (
            not isinstance(node_value_data, dict)
            or "name" not in node_value_data
            or "typed_value_for_var_value" not in node_value_data
        ):
            self.logger.error(f"Cannot format variable node: Invalid value structure: {node.value}")
            return []

        var_name = node_value_data["name"]
        typed_value_instance: TypedValue = node_value_data["typed_value_for_var_value"]

        value_str = typed_value_instance.serialize_for_persistence()

        return [f"({node.type} {format_value(var_name)} {value_str})"]
