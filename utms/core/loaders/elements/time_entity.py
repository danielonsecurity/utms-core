# utms.core.loaders.elements.time_entity.py

from typing import Any, Dict, List, Optional

import hy # Keep for isinstance checks if necessary, though TypedValue handles Hy types

from utms.core.hy.resolvers.elements.time_entity import TimeEntityResolver
from utms.core.loaders.base import ComponentLoader, LoaderContext
from utms.core.managers.elements.time_entity import TimeEntityManager
from utms.core.models.elements.time_entity import TimeEntity # Model class
from utms.core.services.dynamic import DynamicResolutionService
from utms.utils import hy_to_python # Still useful for direct hy_to_python if needed elsewhere

# Import TypedValue and related types
from utms.utms_types import HyNode 
from utms.utms_types.field.types import TypedValue, FieldType, infer_type


class TimeEntityLoader(ComponentLoader[TimeEntity, TimeEntityManager]):
    """Loader for TimeEntity components, creating TimeEntity instances with TypedValue attributes."""

    def __init__(self, manager: TimeEntityManager):
        super().__init__(manager)
        # The resolver is used by the dynamic service
        self._resolver = TimeEntityResolver() 
        self._dynamic_service = DynamicResolutionService(resolver=self._resolver)

    def parse_definitions(self, nodes: List[HyNode]) -> Dict[str, Dict[str, Any]]:
        """
        Parse HyNodes (from entity instance files like tasks/default.hy) 
        into intermediate dictionaries.
        These dictionaries will hold entity properties including 'attributes_typed'
        which is a Dict[str, InitialTypedValueFromPlugin].
        The key of the returned dict is f"{entity_type_str}:{entity_name}".
        """
        parsed_entity_definitions: Dict[str, Dict[str, Any]] = {}

        for node in nodes:
            # Entity instance nodes are expected to have types like "def-task", "def-event" etc.
            # These are set by DynamicTimeEntityPlugin.node_type property.
            # TimeEntityNodePlugin (for "def-time-entity" schema) is processed differently
            # by TimeEntityComponent._extract_entity_types.
            if not node.type.startswith("def-") or node.type == "def-time-entity":
                self.logger.debug(f"Skipping node of type '{node.type}' in TimeEntityLoader.parse_definitions.")
                continue

            entity_instance_name = str(node.value)
            # Get entity_type_name_str (e.g., "task") from the node, set by the plugin
            entity_type_name_str = getattr(node, "entity_type_name_str", None)

            if not entity_type_name_str:
                self.logger.warning(
                    f"Node '{entity_instance_name}' of type '{node.type}' is missing "
                    f"'entity_type_name_str' attribute. Skipping."
                )
                continue
            
            self.logger.debug(
                f"Parsing definition for entity instance: '{entity_instance_name}' of type '{entity_type_name_str}'"
            )

            # Get attributes_typed: Dict[str, InitialTypedValueFromPlugin] from the node
            # This was set by DynamicTimeEntityPlugin.parse
            initial_attributes_typed: Dict[str, TypedValue] = getattr(node, "attributes_typed", {})
            
            self.logger.debug(
                f"  Initial TypedAttributes from plugin for '{entity_instance_name}': "
                f"{ {k: repr(v) for k,v in initial_attributes_typed.items()} }"
            )

            # Store properties needed to create the TimeEntity object later
            entity_props = {
                "name": entity_instance_name,
                "entity_type_str": entity_type_name_str,
                "attributes_typed_initial": initial_attributes_typed, # Store the dict of initial TypedValues
            }

            # Generate a unique key for this definition
            definition_key = f"{entity_type_name_str}:{entity_instance_name}"
            parsed_entity_definitions[definition_key] = entity_props

            self.logger.debug(
                f"  Stored parsed definition for '{definition_key}' with "
                f"{len(initial_attributes_typed)} initial TypedAttributes."
            )
        return parsed_entity_definitions

    def create_object(self, definition_key: str, properties: Dict[str, Any]) -> TimeEntity:
        """
        Create a TimeEntity instance from parsed properties.
        This involves resolving dynamic values and finalizing TypedValue attributes.
        'definition_key' is like "task:My Task".
        'properties' is the dict from parse_definitions.
        """
        entity_instance_name = properties["name"]
        entity_type_name_str = properties["entity_type_str"]
        # This is Dict[str, InitialTypedValueFromPlugin]
        initial_attributes_typed: Dict[str, TypedValue] = properties.get("attributes_typed_initial", {})
        
        self.logger.debug(
            f"Creating TimeEntity object for '{definition_key}' (Name: '{entity_instance_name}', "
            f"Type: '{entity_type_name_str}')"
        )

        final_attributes_for_model: Dict[str, TypedValue] = {}

        for attr_name, initial_typed_value in initial_attributes_typed.items():
            # initial_typed_value.value holds raw Hy object (e.g. hy.Expression) or
            # a Python native if TypedValue._convert_value already processed it for non-CODE static types.
            # initial_typed_value.field_type is from schema.
            # initial_typed_value.is_dynamic tells if it was like `(some-fn)`.
            # initial_typed_value.original has the Hy code string if dynamic.

            self.logger.debug(
                f"  Processing attribute '{attr_name}' for '{entity_instance_name}'. "
                f"Initial TypedValue: {repr(initial_typed_value)}"
            )

            if initial_typed_value.is_dynamic:
                original_hy_expression_string = initial_typed_value.original
                # The value inside initial_typed_value might be the Hy Expression object if field_type was CODE,
                # or a hy_to_python converted list/etc if field_type was (e.g.) DATETIME.
                # It's generally safer to evaluate the original string expression.
                
                if not original_hy_expression_string:
                    self.logger.error(
                        f"Attribute '{attr_name}' for '{definition_key}' is dynamic but has no "
                        f"'original' expression. Using raw value: {initial_typed_value.value}"
                    )
                    # Fallback: use the (likely unconverted or partially converted) value.
                    # This might lead to issues if it's an unresolved HyExpression.
                    # A better TypedValue internal conversion might be needed for this edge case.
                    # For now, we assume .value is the best we have if .original is missing.
                    resolved_python_value = initial_typed_value.value # Potentially problematic
                else:
                    self.logger.debug(
                        f"    Resolving dynamic expression for '{attr_name}': {original_hy_expression_string}"
                    )
                    # The context for evaluation (e.g., access to other entity attributes or global vars)
                    # is handled by the resolver using context passed to evaluate().
                    # self.context.variables provides global variables.
                    evaluation_context_for_resolver = {
                         # Pass variables from the loader's context
                        **(self.context.variables if self.context and self.context.variables else {}),
                        # Could add entity-specific context if resolver needs it, e.g.,
                        # "current_entity_name": entity_instance_name,
                        # "current_entity_type": entity_type_name_str,
                    }

                    # DynamicResolutionService uses the resolver (TimeEntityResolver)
                    resolved_python_value_raw, dynamic_info_obj = self._dynamic_service.evaluate(
                        component_type="time_entity", # Generic type for context
                        component_label=definition_key, # e.g., "task:My Task"
                        attribute=attr_name,
                        expression=original_hy_expression_string, # Evaluate the string
                        # Pass context for variables. Resolver adds more locals.
                        context=evaluation_context_for_resolver 
                    )
                    # Ensure the resolved value is a basic Python type if it came from Hy evaluation
                    resolved_python_value = hy_to_python(resolved_python_value_raw)

                    self.logger.debug(
                        f"    Resolved dynamic '{attr_name}' for '{definition_key}' to: {resolved_python_value} "
                        f"(type: {type(resolved_python_value)})"
                    )
                
                # Create a *new* final TypedValue with the resolved Python value.
                # Preserve schema-defined type, item_type, enum_choices, and dynamic metadata.
                final_field_type = initial_typed_value.field_type
                # If the schema declared it as 'code', but it resolved to a non-string,
                # we might want to update the field_type to reflect the actual resolved type.
                # Or, if schema type is specific (e.g. DATETIME), we trust that.
                if initial_typed_value.field_type == FieldType.CODE and not isinstance(resolved_python_value, str):
                    final_field_type = infer_type(resolved_python_value)
                    self.logger.debug(f"      Field type for '{attr_name}' (was CODE) re-inferred to {final_field_type} after resolution.")


                final_typed_value_for_attr = TypedValue(
                    value=resolved_python_value, 
                    field_type=final_field_type, # Use schema-defined or re-inferred type
                    is_dynamic=True, # It was originally dynamic
                    original=original_hy_expression_string, # Preserve original expression
                    enum_choices=initial_typed_value.enum_choices,
                    item_type=initial_typed_value.item_type
                )
            else: # Attribute is not dynamic
                # The initial_typed_value from the plugin is already suitable.
                # Its .value property should hold the Python native type because
                # TypedValue.__init__ -> _convert_value would have called hy_to_python
                # based on its field_type (unless it was FieldType.CODE with a string literal).
                final_typed_value_for_attr = initial_typed_value
                self.logger.debug(
                    f"    Using static TypedValue for '{attr_name}' "
                    f"(value: {final_typed_value_for_attr.value}, "
                    f"type: {final_typed_value_for_attr.field_type})"
                )

            final_attributes_for_model[attr_name] = final_typed_value_for_attr

        # Create the TimeEntity model instance using the manager.
        # The manager's create method will now receive a dictionary of finalized TypedValues.
        return self._manager.create(
            name=entity_instance_name,
            entity_type=entity_type_name_str,
            attributes=final_attributes_for_model, # Pass Dict[str, FinalTypedValue]
            # dynamic_fields parameter is no longer used for the manager if TimeEntity model changed
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
