from typing import Any, Dict, List, Optional

import hy

from utms.core.hy.utils import (
    hy_obj_to_string,
    python_to_hy_string,
    is_dynamic_content,
)
from utms.core.plugins import NodePlugin
from utms.utils import hy_to_python  # hy_to_python is used by the consumer (EntityComponent)
from utms.utms_types import HyNode

# No TypedValue needed here as this plugin parses schema definitions, not instance data.


class EntityNodePlugin(NodePlugin):
    @property
    def name(self) -> str:
        return "Entity Schema Definition Plugin"  # More precise name

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def node_type(self) -> str:
        return "def-entity"  # This is the Hy form it parses, e.g. (def-entity ...)

    def initialize(self, system_context: Dict[str, Any]):
        pass

    def parse(self, expr: hy.models.Expression) -> Optional[HyNode]:
        """
        Parse a entity schema definition (def-entity ...).
        It extracts the entity type's display name and its attribute schemas.
        """
        if (
            not isinstance(expr, hy.models.Expression) or len(expr) < 2
        ):  # Needs at least (def-entity Name)
            self.logger.warning(f"Invalid def-entity expression: {expr}")
            return None

        entity_type_display_name = str(expr[1])

        # expr[2] is often a "kind" for this definition, e.g., "entity-type" to signify it's a schema.
        # This helps differentiate from actual entity instances if they were ever parsed by a generic plugin.
        # For our specific use, EntityComponent._extract_entity_types filters by this.
        definition_kind = str(expr[2]) if len(expr) > 2 else "unknown-definition"
        # Or raise error if kind is mandatory

        self.logger.debug(
            f"Parsing entity schema: Display Name '{entity_type_display_name}', Kind '{definition_kind}'"
        )

        # This will store attribute schemas as raw Hy objects (Hy Dictionaries)
        # e.g., {'description': <hy.models.Dict {:type "string" ...}>, ...}
        attribute_schemas_raw_hy: Dict[str, hy.models.HyObject] = {}

        # Process each attribute schema definition: (attr_name {:type ... :label ...})
        for attr_schema_expr in expr[3:]:  # Start after def-entity, display_name, kind
            if not (
                isinstance(attr_schema_expr, hy.models.Expression) and len(attr_schema_expr) == 2
            ):
                self.logger.debug(
                    f"  Skipping: {attr_schema_expr} - not a valid attribute schema expression"
                )
                continue

            attr_name_str = str(attr_schema_expr[0])
            # attr_schema_details_hy is the Hy Dict object: {:type "string", :label "Description", ...}
            attr_schema_details_hy = attr_schema_expr[1]

            if not isinstance(attr_schema_details_hy, hy.models.Dict):
                self.logger.warning(
                    f"Attribute schema for '{attr_name_str}' in '{entity_type_display_name}' "
                    f"is not a Hy Dict: {attr_schema_details_hy}. Skipping."
                )
                continue

            self.logger.debug(f"  Attribute Schema: {attr_name_str} = {attr_schema_details_hy}")
            attribute_schemas_raw_hy[attr_name_str] = attr_schema_details_hy

            # is_dynamic_content is not relevant for the schema definition itself.
            # The schema describes attributes, some of which *can be* dynamic in instances.

        self.logger.debug(
            f"Final raw Hy attribute schemas for '{entity_type_display_name}': {attribute_schemas_raw_hy}"
        )

        # Create the HyNode representing this schema definition
        node = HyNode(
            type=self.node_type,  # "def-entity"
            value=entity_type_display_name,  # Store the display name (e.g., "TASK") as the primary value
            original=hy.repr(expr),
            children=[],  # This node doesn't need children in this context; info is on attributes
        )

        # Attach the kind of definition and the raw attribute schemas as custom properties.
        # The EntityComponent will use these.
        setattr(node, "definition_kind", definition_kind)  # e.g., "entity-type"
        setattr(node, "attribute_schemas_raw_hy", attribute_schemas_raw_hy)

        self.logger.debug(
            f"Created HyNode for schema '{entity_type_display_name}' with "
            f"{len(attribute_schemas_raw_hy)} attribute schema definitions."
        )
        return node

    def format(self, node: HyNode) -> List[str]:
        """Format a entity schema definition HyNode back to Hy code."""
        value = node.value
        if isinstance(value, hy.models.Object):
            entity_type_display_name = hy_obj_to_string(value)
        else:
            entity_type_display_name = python_to_hy_string(value)
        definition_kind = getattr(node, "definition_kind", "entity-type")  # Default back

        lines = [f"({self.node_type} {entity_type_display_name} {definition_kind}"]

        attribute_schemas_raw_hy: Optional[Dict[str, hy.models.HyObject]] = getattr(
            node, "attribute_schemas_raw_hy", None
        )

        if attribute_schemas_raw_hy:
            for attr_name, attr_schema_hy_obj in attribute_schemas_raw_hy.items():
                schema_details_str = hy_obj_to_string(attr_schema_hy_obj)
                lines.append(f"  ({attr_name} {schema_details_str})")

        lines.append(")")
        return lines
