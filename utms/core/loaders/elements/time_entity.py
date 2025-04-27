from typing import Any, Dict, List, Optional

import hy

from utms.core.hy.resolvers.elements.time_entity import TimeEntityResolver
from utms.core.loaders.base import ComponentLoader, LoaderContext
from utms.core.managers.elements.time_entity import TimeEntityManager
from utms.core.models.elements.time_entity import TimeEntity
from utms.core.services.dynamic import DynamicResolutionService
from utms.utils import hy_to_python
from utms.utms_types import HyNode


class TimeEntityLoader(ComponentLoader[TimeEntity, TimeEntityManager]):
    """Loader for TimeEntity components."""

    def __init__(self, manager: TimeEntityManager):
        super().__init__(manager)
        self._resolver = TimeEntityResolver()
        self._dynamic_service = DynamicResolutionService(resolver=self._resolver)

    def parse_definitions(self, nodes: List[HyNode]) -> Dict[str, dict]:
        """Parse HyNodes into time entity definitions."""
        entities = {}

        for node in nodes:
            # Check if this is a time entity node (either def-time-entity or a dynamic type like def-task)
            if node.type == "def-time-entity":
                entity_name = node.value
                entity_type = getattr(node, "entity_type", "generic")
            elif node.type.startswith("def-"):
                # For dynamic types (def-task, def-habit, etc.), extract the entity type from the node type
                entity_name = node.value
                entity_type = node.type[4:]  # Remove 'def-' prefix
            else:
                # Skip nodes that aren't time entity definitions
                continue

            self.logger.debug("Processing node: %s of type %s", entity_name, entity_type)

            # Get attributes and dynamic fields from the node
            attributes = getattr(node, "attributes", {})
            dynamic_fields = getattr(node, "dynamic_fields", {})

            self.logger.debug("Node attributes in loader: %s", attributes)
            self.logger.debug("Node dynamic fields in loader: %s", dynamic_fields)
            self.logger.debug(f"Node has {len(attributes)} attributes")

            # Initialize entity properties
            entity_props = {
                "name": entity_name,
                "entity_type": entity_type,
                "attributes": attributes,
                "dynamic_fields": dynamic_fields
            }

            # Generate a unique key for the entity
            key = f"{entity_type}:{entity_name}"
            entities[key] = entity_props

            self.logger.debug(f"Added entity {key} with attributes: {entity_props['attributes']}")

        return entities

    def create_object(self, key: str, properties: Dict[str, Any]) -> TimeEntity:
        """Create a TimeEntity from properties."""
        # Extract entity properties
        name = properties["name"]
        entity_type = properties["entity_type"]
        attributes = properties.get("attributes", {})
        dynamic_fields = properties.get("dynamic_fields", {})
        
        self.logger.debug(f"Creating time entity {name} of type {entity_type}")
        self.logger.debug(f"Attributes: {attributes}")
        self.logger.debug(f"Dynamic fields: {dynamic_fields}")

        # Resolve dynamic expressions for each field
        for field_name, field_info in dynamic_fields.items():
            original_expr = field_info["original"]
            field_value = attributes.get(field_name)
            
            # Only resolve if it's an expression
            if isinstance(field_value, (hy.models.Expression, hy.models.Symbol)):
                resolved_value, dynamic_info = self._dynamic_service.evaluate(
                    component_type="time_entity",
                    component_label=key,
                    attribute=field_name,
                    expression=field_value,
                    context=self.context.variables if self.context else None,
                )
                self.logger.debug(f"Resolved dynamic {field_name} for {key}: {resolved_value}")
                
                # Update the value in attributes
                attributes[field_name] = hy_to_python(resolved_value)
                
                # Update the dynamic field info
                dynamic_fields[field_name]["value"] = attributes[field_name]
            else:
                self.logger.debug(f"Using static {field_name} for {key}: {field_value}")
                attributes[field_name] = hy_to_python(field_value)

        # Create time entity object
        return self._manager.create(
            name=name,
            entity_type=entity_type,
            attributes=attributes,
            dynamic_fields=dynamic_fields,
        )

    def process(self, nodes: List[HyNode], context: LoaderContext) -> Dict[str, TimeEntity]:
        """Process time entity nodes into TimeEntity objects."""
        # First, parse definitions
        definitions = self.parse_definitions(nodes)

        # Process entities
        objects = {}
        for key, properties in definitions.items():
            try:
                # Create the entity
                obj = self.create_object(key, properties)
                objects[key] = obj
                
                # Update context if needed
                if context and hasattr(context, "time_entities") and context.time_entities is not None:
                    context.time_entities[key] = obj
                
            except Exception as e:
                self.logger.error(f"Error processing time entity {key}: {e}")
                raise

        # Load all objects into manager
        self._manager.load_objects(objects)

        return objects
