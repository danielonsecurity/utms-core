from typing import Any, Dict, List, Optional

import hy

from utms.core.hy.utils import format_value
from utms.core.mixins.base import LoggerMixin
from utms.core.plugins.base import NodePlugin
from utms.utms_types import HyNode


class ComplexTypeNodePlugin(NodePlugin, LoggerMixin):
    """
    Plugin to parse complex type schema definitions (def-complex-type ...).
    These definitions are for reusable structured data types that can be used
    as items in lists or values in dictionaries within entity attributes.
    """

    @property
    def name(self) -> str:
        return "Complex Type Schema Definition Plugin"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def node_type(self) -> str:
        return "def-complex-type"

    def initialize(self, system_context: Dict[str, Any]):
        self.logger.debug(f"Plugin '{self.name}' initialized.")
        pass

    def parse(self, expr: hy.models.Expression) -> Optional[HyNode]:
        """
        Parse a complex type schema definition (def-complex-type "NAME" (field1 {...}) ...).
        """
        if not isinstance(expr, hy.models.Expression) or len(expr) < 2:
            self.logger.warning(f"Invalid def-complex-type expression: {expr}")
            return None

        complex_type_name = str(expr[1])

        self.logger.debug(f"Parsing complex type schema: Name '{complex_type_name}'")

        attribute_schemas_raw_hy: Dict[str, hy.models.HyObject] = {}

        for attr_schema_expr in expr[2:]:
            if not (
                isinstance(attr_schema_expr, hy.models.Expression) and len(attr_schema_expr) == 2
            ):
                self.logger.debug(
                    f"  Skipping: {attr_schema_expr} - not a valid attribute schema expression for complex type"
                )
                continue

            attr_name_str = str(attr_schema_expr[0])
            attr_schema_details_hy = attr_schema_expr[1]

            if not isinstance(attr_schema_details_hy, hy.models.Dict):
                self.logger.warning(
                    f"Attribute schema for '{attr_name_str}' in complex type '{complex_type_name}' "
                    f"is not a Hy Dict: {attr_schema_details_hy}. Skipping."
                )
                continue

            self.logger.debug(
                f"  Complex Type Attribute Schema: {attr_name_str} = {hy.repr(attr_schema_details_hy)}"
            )
            attribute_schemas_raw_hy[attr_name_str] = attr_schema_details_hy

        self.logger.debug(
            f"Final raw Hy attribute schemas for complex type '{complex_type_name}': {len(attribute_schemas_raw_hy)} attributes found."
        )

        node = HyNode(
            type=self.node_type, value=complex_type_name, original=hy.repr(expr), children=[]
        )

        setattr(node, "attribute_schemas_raw_hy", attribute_schemas_raw_hy)

        self.logger.debug(
            f"Created HyNode for complex type schema '{complex_type_name}' with "
            f"{len(attribute_schemas_raw_hy)} attribute schema definitions."
        )
        return node

    def format(self, node: HyNode) -> List[str]:
        """Format a complex type schema definition HyNode back to Hy code."""
        complex_type_name_str = format_value(node.value)  # Ensures quotes if needed
        lines = [f"({self.node_type} {complex_type_name_str}"]

        attribute_schemas_raw_hy: Optional[Dict[str, hy.models.HyObject]] = getattr(
            node, "attribute_schemas_raw_hy", None
        )

        if attribute_schemas_raw_hy:
            for attr_name in sorted(attribute_schemas_raw_hy.keys()):
                attr_schema_hy_obj = attribute_schemas_raw_hy[attr_name]
                schema_details_str = hy.repr(attr_schema_hy_obj)
                lines.append(f"  ({attr_name} {schema_details_str})")

        lines.append(")")
        return lines
