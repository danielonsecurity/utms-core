# utms.core.plugins.elements.time_entity.py

from typing import Any, Dict, List, Optional

import hy

from utms.core.hy.utils import format_value, is_dynamic_content # is_dynamic_content might not be relevant here
from utms.core.plugins import NodePlugin
from utms.utils import hy_to_python # hy_to_python is used by the consumer (TimeEntityComponent)
from utms.utms_types import HyNode
# No TypedValue needed here as this plugin parses schema definitions, not instance data.

class TimeEntityNodePlugin(NodePlugin):
    @property
    def name(self) -> str:
        return "Time Entity Schema Definition Plugin" # More precise name

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def node_type(self) -> str:
        return "def-time-entity" # This is the Hy form it parses, e.g. (def-time-entity ...)

    def initialize(self, system_context: Dict[str, Any]):
        pass

    def parse(self, expr: hy.models.Expression) -> Optional[HyNode]:
        """
        Parse a time entity schema definition (def-time-entity ...).
        It extracts the entity type's display name and its attribute schemas.
        """
        if not isinstance(expr, hy.models.Expression) or len(expr) < 2: # Needs at least (def-time-entity Name)
            self.logger.warning(f"Invalid def-time-entity expression: {expr}")
            return None

        # expr[0] is 'def-time-entity'
        # expr[1] is the Entity Type Display Name (e.g., TASK, EVENT). This will be used as the key in TimeEntityComponent.entity_types
        entity_type_display_name = str(expr[1])

        # expr[2] is often a "kind" for this definition, e.g., "entity-type" to signify it's a schema.
        # This helps differentiate from actual entity instances if they were ever parsed by a generic plugin.
        # For our specific use, TimeEntityComponent._extract_entity_types filters by this.
        definition_kind = str(expr[2]) if len(expr) > 2 else "unknown-definition" 
                                                        # Or raise error if kind is mandatory

        self.logger.debug(
            f"Parsing time entity schema: Display Name '{entity_type_display_name}', Kind '{definition_kind}'"
        )
        
        # This will store attribute schemas as raw Hy objects (Hy Dictionaries)
        # e.g., {'description': <hy.models.Dict {:type "string" ...}>, ...}
        attribute_schemas_raw_hy: Dict[str, hy.models.HyObject] = {}

        # Process each attribute schema definition: (attr_name {:type ... :label ...})
        for attr_schema_expr in expr[3:]: # Start after def-time-entity, display_name, kind
            if not (isinstance(attr_schema_expr, hy.models.Expression) and len(attr_schema_expr) == 2):
                self.logger.debug(f"  Skipping: {attr_schema_expr} - not a valid attribute schema expression")
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

        self.logger.debug(f"Final raw Hy attribute schemas for '{entity_type_display_name}': {attribute_schemas_raw_hy}")

        # Create the HyNode representing this schema definition
        node = HyNode(
            type=self.node_type, # "def-time-entity"
            value=entity_type_display_name, # Store the display name (e.g., "TASK") as the primary value
            original=hy.repr(expr),
            children=[] # This node doesn't need children in this context; info is on attributes
        )

        # Attach the kind of definition and the raw attribute schemas as custom properties.
        # The TimeEntityComponent will use these.
        setattr(node, "definition_kind", definition_kind) # e.g., "entity-type"
        setattr(node, "attribute_schemas_raw_hy", attribute_schemas_raw_hy)

        self.logger.debug(
             f"Created HyNode for schema '{entity_type_display_name}' with "
             f"{len(attribute_schemas_raw_hy)} attribute schema definitions."
        )
        return node

    def format(self, node: HyNode) -> List[str]:
        """Format a time entity schema definition HyNode back to Hy code."""
        # This node is one produced by parse()
        entity_type_display_name = format_value(node.value) # e.g., "TASK" -> "\"TASK\"" if needed
        definition_kind = getattr(node, "definition_kind", "entity-type") # Default back
        
        lines = [f"({self.node_type} {entity_type_display_name} {definition_kind}"]

        attribute_schemas_raw_hy: Optional[Dict[str, hy.models.HyObject]] = getattr(node, "attribute_schemas_raw_hy", None)

        if attribute_schemas_raw_hy:
            for attr_name, attr_schema_hy_obj in attribute_schemas_raw_hy.items():
                # attr_schema_hy_obj is a hy.models.Dict. format_value should handle it.
                # hy.repr() is also an option if format_value isn't perfect for Hy dicts.
                schema_details_str = format_value(attr_schema_hy_obj) 
                lines.append(f"  ({attr_name} {schema_details_str})")
        
        lines.append(")")
        return lines
