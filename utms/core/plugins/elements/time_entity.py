from typing import Any, Dict, List

import hy

from utms.core.hy.utils import format_value, is_dynamic_content
from utms.core.plugins import NodePlugin
from utms.utils import hy_to_python
from utms.utms_types import HyNode


class TimeEntityNodePlugin(NodePlugin):
    @property
    def name(self) -> str:
        return "Time Entity Node Plugin"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def node_type(self) -> str:
        return "def-time-entity"

    def initialize(self, system_context: Dict[str, Any]):
        pass

    def parse(self, expr) -> HyNode:
        """Parse time entity definition."""
        if len(expr) < 3:
            return None

        entity_name = str(expr[1])
        entity_type = str(expr[2]) if len(expr) > 2 else "generic"

        self.logger.debug(f"Parsing time entity {entity_name} of type {entity_type}")
        self.logger.debug(f"Expression: {expr}")

        # Create a dictionary to store attributes
        attributes = {}
        dynamic_fields = {}

        # Process each attribute definition
        for i in range(3, len(expr)):
            # Check if it's a Hy expression (which it should be)
            if isinstance(expr[i], hy.models.Expression) and len(expr[i]) >= 2:
                attr_name = str(expr[i][0])
                attr_value = expr[i][1]

                self.logger.debug(f"  Attribute: {attr_name} = {attr_value}")

                # Store the attribute value
                attributes[attr_name] = attr_value

                # Check if the value is dynamic
                if is_dynamic_content(attr_value):
                    dynamic_fields[attr_name] = {
                        "original": hy.repr(attr_value).strip("'"),
                        "value": attr_value
                    }
            else:
                self.logger.debug(f"  Skipping: {expr[i]} - not a valid attribute expression")

        self.logger.debug(f"Final attributes: {attributes}")
        self.logger.debug(f"Final dynamic fields: {dynamic_fields}")

        # Create the main time entity node
        node = HyNode(
            type="def-time-entity",
            value=entity_name,
            original=hy.repr(expr),
        )

        # Add entity_type and attributes as custom properties
        setattr(node, "entity_type", entity_type)
        setattr(node, "attributes", attributes)
        setattr(node, "dynamic_fields", dynamic_fields)

        self.logger.debug(f"Created node with {len(attributes)} attributes")
        return node


    def format(self, node: HyNode) -> List[str]:
        """Format time entity definition back to Hy code."""
        entity_type = getattr(node, "entity_type", "generic")
        attributes = getattr(node, "attributes", {})
        dynamic_fields = getattr(node, "dynamic_fields", {})

        if not attributes:
            return [f"(def-time-entity {node.value} {entity_type})"]

        lines = [f"(def-time-entity {node.value} {entity_type}"]

        # Format each attribute
        for field_name, value in attributes.items():
            # Format the value based on whether it's dynamic
            if field_name in dynamic_fields:
                value_str = dynamic_fields[field_name]["original"]
            else:
                value_str = format_value(value)

            lines.append(f"  ({field_name} {value_str})")

        lines.append(")")
        return lines
