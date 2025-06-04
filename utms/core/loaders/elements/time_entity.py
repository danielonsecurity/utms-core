# utms.core.loaders.elements.time_entity.py

from typing import Any, Dict, List, Optional

import hy

from utms.core.hy.resolvers.elements.time_entity import TimeEntityResolver
from utms.core.loaders.base import ComponentLoader, LoaderContext  # Updated LoaderContext
from utms.core.managers.elements.time_entity import TimeEntityManager  # Updated manager
from utms.core.models.elements.time_entity import TimeEntity  # Updated model
from utms.core.services.dynamic import DynamicResolutionService
from utms.utils import hy_to_python
from utms.utms_types import HyNode
from utms.utms_types.field.types import FieldType, TypedValue, infer_type


class TimeEntityLoader(ComponentLoader[TimeEntity, TimeEntityManager]):
    """Loader for TimeEntity components, creating TimeEntity instances with TypedValue attributes and category awareness."""

    def __init__(self, manager: TimeEntityManager):
        super().__init__(manager)
        self._resolver = TimeEntityResolver()
        self._dynamic_service = DynamicResolutionService(resolver=self._resolver)

    def parse_definitions(self, nodes: List[HyNode]) -> Dict[str, Dict[str, Any]]:
        """
        Parse HyNodes from an entity instance file.
        The context (self.context) is expected to have current_entity_type and current_category.
        The key of the returned dict (the 'label' for create_object) will be f"{entity_type}:{category}:{name}".
        """
        parsed_entity_definitions: Dict[str, Dict[str, Any]] = {}

        if not self.context:
            self.logger.critical(
                "LoaderContext not available in TimeEntityLoader.parse_definitions. This is a programming error."
            )
            return parsed_entity_definitions

        # Get entity_type and category from the context set by TimeEntityComponent
        current_entity_type_from_context = self.context.current_entity_type
        current_category_from_context = (
            self.context.current_category or "default"
        )  # Default if None

        if not current_entity_type_from_context:
            self.logger.error(
                "current_entity_type missing in LoaderContext for TimeEntityLoader. Cannot process nodes."
            )
            return parsed_entity_definitions

        self.logger.debug(
            f"TimeEntityLoader.parse_definitions for type: '{current_entity_type_from_context}', category: '{current_category_from_context}'"
        )

        for node in nodes:
            # Plugin should have set node.type to "def-<entity_type_str>" (e.g., "def-task")
            # and node.entity_type_name_str to "<entity_type_str>" (e.g., "task")

            expected_node_type = f"def-{current_entity_type_from_context.lower()}"
            if node.type != expected_node_type:
                self.logger.warning(
                    f"Skipping node with type '{node.type}'. Expected '{expected_node_type}' "
                    f"for current context (type: '{current_entity_type_from_context}', category: '{current_category_from_context}')."
                )
                continue

            entity_instance_name = str(node.value)
            # This was set by DynamicTimeEntityPlugin.parse based on its own _entity_type_str
            node_entity_type_str_from_plugin = getattr(node, "entity_type_name_str", None)

            if node_entity_type_str_from_plugin != current_entity_type_from_context:
                self.logger.warning(
                    f"Node's declared entity type '{node_entity_type_str_from_plugin}' "
                    f"does not match context's entity type '{current_entity_type_from_context}'. "
                    f"Instance: '{entity_instance_name}', Category: '{current_category_from_context}'. Skipping."
                )
                continue

            self.logger.debug(f"  Parsing definition for instance: '{entity_instance_name}'")

            initial_attributes_typed: Dict[str, TypedValue] = getattr(node, "attributes_typed", {})

            entity_props = {
                "name": entity_instance_name,
                "entity_type_str": current_entity_type_from_context,
                "category_str": current_category_from_context,
                "attributes_typed_initial": initial_attributes_typed,
            }

            # Use a unique label for create_object, including category
            # This label is used as the key in the dict returned by process()
            # and subsequently by manager.load_objects() if manager uses these keys.
            # The TimeEntityManager's internal keying is separate (currently type:name).
            definition_processing_key = f"{current_entity_type_from_context}:{current_category_from_context}:{entity_instance_name}"
            parsed_entity_definitions[definition_processing_key] = entity_props

        return parsed_entity_definitions

    def create_object(
        self, definition_processing_key: str, properties: Dict[str, Any]
    ) -> TimeEntity:
        """
        Create a TimeEntity instance.
        'definition_processing_key' is like "task:work:My Task".
        'properties' contains name, entity_type_str, category_str, and attributes_typed_initial.
        """
        entity_instance_name = properties["name"]
        entity_type_name_str = properties["entity_type_str"]
        category_name_str = properties["category_str"]
        initial_attributes_typed: Dict[str, TypedValue] = properties.get(
            "attributes_typed_initial", {}
        )

        self.logger.debug(
            f"Creating TimeEntity: '{definition_processing_key}' (Name: '{entity_instance_name}', "
            f"Type: '{entity_type_name_str}', Category: '{category_name_str}')"
        )

        final_attributes_for_model: Dict[str, TypedValue] = {}
        # Ensure context and variables are available for dynamic service
        evaluation_context_for_resolver = {}
        if self.context and self.context.variables:
            evaluation_context_for_resolver.update(self.context.variables)
        # Add entity-specific context for resolver if it uses it (e.g. self-referential attributes)
        # evaluation_context_for_resolver["current_entity_name"] = entity_instance_name
        # evaluation_context_for_resolver["current_entity_type"] = entity_type_name_str
        # evaluation_context_for_resolver["current_category"] = category_name_str

        for attr_name, initial_typed_value in initial_attributes_typed.items():
            self.logger.debug(
                f"  Processing attribute '{attr_name}'. Initial TypedValue from plugin: {repr(initial_typed_value)}"
            )
            if initial_typed_value.is_dynamic:
                original_hy_expression_string = initial_typed_value.original
                if not original_hy_expression_string:
                    self.logger.error(
                        f"Attribute '{attr_name}' for '{definition_processing_key}' is dynamic but has no 'original' expression. "
                        f"Using raw plugin value: {initial_typed_value.value}"
                    )
                    resolved_python_value = initial_typed_value.value
                else:
                    self.logger.debug(
                        f"    Resolving dynamic expr for '{attr_name}': {original_hy_expression_string}"
                    )
                    resolved_val_raw, _ = self._dynamic_service.evaluate(
                        expression=original_hy_expression_string,
                        context=evaluation_context_for_resolver,
                        component_type="time_entity",
                        component_label=f"{entity_type_name_str}:{category_name_str}:{entity_instance_name}",
                        attribute=attr_name,
                    )
                    resolved_python_value = hy_to_python(resolved_val_raw)
                    self.logger.debug(
                        f"    Resolved to: {resolved_python_value} (type: {type(resolved_python_value)})"
                    )

                # Determine final field_type for TypedValue, potentially re-inferring from resolved value
                final_field_type_for_tv = initial_typed_value.field_type
                if initial_typed_value.field_type == FieldType.CODE and not isinstance(
                    resolved_python_value, str
                ):
                    final_field_type_for_tv = infer_type(resolved_python_value)
                    self.logger.debug(
                        f"      Field type for '{attr_name}' (was {initial_typed_value.field_type}) re-inferred to {final_field_type_for_tv}."
                    )

                final_typed_value_for_attr = TypedValue(
                    value=resolved_python_value,
                    field_type=final_field_type_for_tv,
                    is_dynamic=True,
                    original=original_hy_expression_string,
                    enum_choices=initial_typed_value.enum_choices,
                    item_type=initial_typed_value.item_type,
                )
            else:
                # For static values, the TypedValue from plugin (after its internal _convert_value) is final.
                final_typed_value_for_attr = initial_typed_value
                self.logger.debug(
                    f"    Using static TypedValue for '{attr_name}' (value: {final_typed_value_for_attr.value})"
                )

            final_attributes_for_model[attr_name] = final_typed_value_for_attr

        # Manager's create method now accepts 'category'
        return self._manager.create(
            name=entity_instance_name,
            entity_type=entity_type_name_str,
            category=category_name_str,
            attributes=final_attributes_for_model,
        )
