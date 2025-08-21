from typing import Any, Dict, List, Optional

import hy

from utms.core.hy.utils import is_dynamic_content
from utms.core.mixins.base import LoggerMixin
from utms.core.plugins.base import NodePlugin
from utms.utms_types import HyNode
from utms.utms_types.field.types import FieldType, TypedValue, infer_type
from utms.core.hy.converter import converter


class LogContextNodePlugin(NodePlugin, LoggerMixin):
    """
    Plugin to parse and format a single context log entry.
    e.g., (log-context "Work" :start_time ... :end_time ...)
    """

    @property
    def name(self) -> str:
        return "Context Log Entry Plugin"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def node_type(self) -> str:
        return "log-context"

    def initialize(self, system_context: Dict[str, Any]):
        pass

    def parse(self, expr: hy.models.Expression) -> Optional[HyNode]:
        """

        Parses a (log-context "Name" :key_1 val_1 ...) expression.
        The parsed data is stored as TypedValue attributes on the HyNode.
        """
        if not isinstance(expr, hy.models.Expression) or len(expr) < 2:
            self.logger.warning(f"Invalid log-context expression: {expr}")
            return None

        context_name = str(expr[1])
        attributes_typed = {}
        kwargs_exprs = expr[2:]

        it = iter(kwargs_exprs)
        try:
            while True:
                key_keyword = next(it)
                val_object = next(it)
                attr_name = str(key_keyword).lstrip(":")
                original_str = converter.model_to_string(val_object)

                attributes_typed[attr_name] = TypedValue(
                    value=val_object,
                    field_type=infer_type(val_object),
                    is_dynamic=is_dynamic_content(val_object),
                    original=original_str,
                )
        except StopIteration:
            pass

        node = HyNode(type=self.node_type, value=context_name, original=converter.model_to_string(expr))
        setattr(node, "attributes_typed", attributes_typed)
        return node

    def format(self, node: HyNode) -> List[str]:
        """Formats a log-context HyNode back into a Hy s-expression."""
        value = node.value
        if isinstance(value, hy.models.Object):
            context_name_str = converter.model_to_string(value)
        else:
            context_name_str = converter.py_to_string(value)

        parts = [f"({self.node_type} {context_name_str}"]

        attributes_typed: Optional[Dict[str, TypedValue]] = getattr(node, "attributes_typed", None)
        if attributes_typed:
            for attr_name in sorted(attributes_typed.keys()):
                typed_value = attributes_typed[attr_name]
                value_str = typed_value.serialize_for_persistence()
                parts.append(f"  :{attr_name} {value_str}")

        line = " ".join(parts) + ")"
        return [line]
