from types import SimpleNamespace
from typing import Any, Dict, List, Optional

import hy
from hy.models import Expression, Symbol

from utms.core.hy.resolvers.elements.entity import EntityResolver
from utms.core.hy.utils import is_dynamic_content, get_from_hy_dict
from utms.core.loaders.base import ComponentLoader, LoaderContext
from utms.core.managers.elements.entity import EntityManager
from utms.core.models.elements.entity import Entity
from utms.core.services.dynamic import DynamicResolutionService, dynamic_resolution_service
from utms.utils import hy_to_python, py_list_to_hy_expression
from utms.utms_types import HyNode
from utms.utms_types.field.types import FieldType, TypedValue, infer_type


def python_value_to_hy_repr_string_for_original(value: Any) -> str:
    """
    Creates a string representation of a Python value that resembles its
    original Hy source, intended for the 'original' field of a TypedValue
    when processing static schema defaults.
    """
    if value is None:
        return "None"
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, str):
        return hy.repr(hy.models.String(value))
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, hy.models.Object):
        return hy.repr(value)
    return str(value)


class EntityLoader(ComponentLoader[Entity, EntityManager]):
    def __init__(self, manager: EntityManager):
        super().__init__(manager)
        self._resolver = EntityResolver(entity_manager=self._manager)
        self._dynamic_service = DynamicResolutionService(resolver=self._resolver)

    def _get_entity_schema(self, entity_type_str: str) -> Optional[Dict[str, Any]]:
        if (
            self.context
            and hasattr(self.context, "current_entity_schema")
            and self.context.current_entity_type == entity_type_str.lower()
        ):
            return self.context.current_entity_schema
        self.logger.warning(
            f"Schema for entity type '{entity_type_str}' not found in LoaderContext."
        )
        return None

    def parse_definitions(self, nodes: List[HyNode]) -> Dict[str, Dict[str, Any]]:
        parsed_entity_definitions: Dict[str, Dict[str, Any]] = {}
        if not self.context:
            self.logger.critical("LoaderContext not available in EntityLoader.parse_definitions.")
            return parsed_entity_definitions

        current_entity_type_from_context = self.context.current_entity_type
        current_category_from_context = self.context.current_category or "default"

        if not current_entity_type_from_context:
            self.logger.error("current_entity_type missing in LoaderContext for EntityLoader.")
            return parsed_entity_definitions

        for node in nodes:
            expected_node_type = f"def-{current_entity_type_from_context.lower()}"
            if node.type != expected_node_type:
                continue

            entity_instance_name = str(node.value)
            node_entity_type_str_from_plugin = getattr(node, "entity_type_name_str", None)
            if node_entity_type_str_from_plugin != current_entity_type_from_context:
                continue

            initial_attributes_typed: Dict[str, TypedValue] = getattr(node, "attributes_typed", {})
            entity_props = {
                "name": entity_instance_name,
                "entity_type_str": current_entity_type_from_context,
                "category_str": current_category_from_context,
                "attributes_typed_initial": initial_attributes_typed,
            }
            definition_processing_key = f"{current_entity_type_from_context}:{current_category_from_context}:{entity_instance_name}"
            parsed_entity_definitions[definition_processing_key] = entity_props
        return parsed_entity_definitions

    def create_object(self, definition_processing_key: str, properties: Dict[str, Any]) -> Entity:
        entity_instance_name = properties["name"]
        entity_type_name_str = properties["entity_type_str"]
        category_name_str = properties["category_str"]
        initial_attributes_typed: Dict[str, TypedValue] = properties.get(
            "attributes_typed_initial", {}
        )

        self.logger.debug(f"Creating Entity: '{definition_processing_key}'")

        final_attributes_for_model: Dict[str, TypedValue] = {}
        current_entity_py_attributes_for_self: Dict[str, Any] = {}
        global_variables_for_evaluation = (
            self.context.variables if self.context and self.context.variables else {}
        )

        entity_schema = self._get_entity_schema(entity_type_name_str)
        if not entity_schema:
            self.logger.error(
                f"Schema not found for '{entity_type_name_str}'. Default value processing will fail."
            )
            entity_schema = {}

        self_object_for_eval = SimpleNamespace(**current_entity_py_attributes_for_self)
        attributes_processed_from_instance = set()

        # Pass 1: Attributes explicitly defined in the instance .hy file
        for attr_name, initial_typed_value in initial_attributes_typed.items():
            attr_schema_details = entity_schema.get(attr_name, hy.models.Dict())
            declared_type_hy_obj = get_from_hy_dict(attr_schema_details, "type")
            declared_type_str = hy_to_python(declared_type_hy_obj)
            if declared_type_str == "code":
                final_attributes_for_model[attr_name] = initial_typed_value
                self.logger.debug(
                    f"  Preserving hook '{attr_name}' as-is: {initial_typed_value.original}"
                )
                current_entity_py_attributes_for_self[attr_name] = initial_typed_value.value
                setattr(self_object_for_eval, attr_name, initial_typed_value.value)

                continue
            attributes_processed_from_instance.add(attr_name)
            resolved_python_value: Any
            final_original_str = initial_typed_value.original  # String from plugin
            current_field_type = initial_typed_value.field_type

            if not initial_typed_value.is_dynamic:
                resolved_python_value = initial_typed_value.value
                final_attributes_for_model[attr_name] = initial_typed_value
            else:
                context_for_dynamic_service = {
                    **global_variables_for_evaluation,
                    "self": self_object_for_eval,
                }
                raw_hy_object_to_evaluate = initial_typed_value._raw_value
                resolved_val_raw, _ = self._dynamic_service.evaluate(
                    expression=raw_hy_object_to_evaluate,
                    context=context_for_dynamic_service,
                    component_type="entity_attribute",
                    component_label=f"{entity_type_name_str}:{category_name_str}:{entity_instance_name}",
                    attribute=attr_name,
                )
                resolved_python_value = hy_to_python(resolved_val_raw)
                # Use schema-defined type if available, else infer from resolved value
                attr_schema_details_for_type = entity_schema.get(attr_name, {})
                type_from_schema = hy_to_python(get_from_hy_dict(attr_schema_details_for_type,"type"))
                current_field_type = (
                    FieldType.from_string(type_from_schema)
                    if type_from_schema
                    else infer_type(resolved_python_value)
                )

                final_attributes_for_model[attr_name] = TypedValue(
                    value=resolved_python_value,
                    field_type=current_field_type,
                    is_dynamic=True,
                    original=final_original_str,
                    item_type=initial_typed_value.item_type,
                    enum_choices=initial_typed_value.enum_choices,
                    item_schema_type=initial_typed_value.item_schema_type,
                    referenced_entity_type=initial_typed_value.referenced_entity_type,
                    referenced_entity_category=initial_typed_value.referenced_entity_category,
                )

            current_entity_py_attributes_for_self[attr_name] = resolved_python_value
            setattr(self_object_for_eval, attr_name, resolved_python_value)
            self.logger.debug(
                f"  Processed instance attribute '{attr_name}'. Value: {repr(resolved_python_value)}"
            )

        # Pass 2: Apply defaults for schema attributes not provided in the instance
        for schema_attr_name, attr_schema_details in entity_schema.items():
            if schema_attr_name in attributes_processed_from_instance:
                continue

            default_value_from_schema_hy_obj = get_from_hy_dict(attr_schema_details, "default_value")
            default_value_from_schema = hy_to_python(default_value_from_schema_hy_obj)

            if get_from_hy_dict(attr_schema_details, "default_value") is None:
                required_hy_obj = get_from_hy_dict(attr_schema_details, "required")
                if hy_to_python(required_hy_obj) == True: # Check the python value
                    self.logger.error(
                        f"Missing required attribute '{schema_attr_name}' for '{definition_processing_key}' and no default provided."
                    )
                continue
                
            declared_field_type_str = hy_to_python(get_from_hy_dict(attr_schema_details, "type", "string"))
            declared_field_type = FieldType.from_string(declared_field_type_str)

            parsed_default_for_tv: Any
            is_default_expr_dynamic = False

            original_for_default_tv: Optional[str] = None # Initialize the variable

            if isinstance(
                default_value_from_schema, str
            ) and default_value_from_schema.strip().startswith("("):
                parsed_default_for_tv = hy.read(default_value_from_schema.strip())
                is_default_expr_dynamic = is_dynamic_content(parsed_default_for_tv)
            elif isinstance(default_value_from_schema, list):
                try:
                    # Rehydrate list back to a HyExpression to check if it's dynamic
                    potential_hy_expr = py_list_to_hy_expression(default_value_from_schema)
                    if is_dynamic_content(potential_hy_expr):
                        parsed_default_for_tv = potential_hy_expr
                        is_default_expr_dynamic = True
                        # Update original string to reflect the rehydrated expression
                        original_for_default_tv = hy.repr(parsed_default_for_tv)
                    else:
                        # It's a list, but not dynamic, so treat as a static list value
                        parsed_default_for_tv = default_value_from_schema
                        is_default_expr_dynamic = False
                except Exception as e_rebuild:
                    self.logger.error(
                        f"Could not rebuild HyExpr from list for default '{schema_attr_name}': {e_rebuild}. Treating as literal list."
                    )
                    parsed_default_for_tv = default_value_from_schema
                    is_default_expr_dynamic = False
            else:  # Python native literal (int, str, bool, None, list, dict)
                parsed_default_for_tv = default_value_from_schema
                is_default_expr_dynamic = False

            resolved_default_python_value: Any
            if is_default_expr_dynamic:
                context_for_dynamic_service = {
                    **global_variables_for_evaluation,
                    "self": self_object_for_eval,
                }
                resolved_raw, _ = self._dynamic_service.evaluate(
                    expression=parsed_default_for_tv,
                    context=context_for_dynamic_service,
                    component_type="entity_default",
                    component_label=f"{entity_type_name_str}:{category_name_str}:{entity_instance_name}",
                    attribute=schema_attr_name,
                )
                resolved_default_python_value = hy_to_python(resolved_raw)
            else:
                resolved_default_python_value = parsed_default_for_tv

            if (
                declared_field_type in (FieldType.DATETIME, FieldType.ENTITY_REFERENCE)
                and resolved_default_python_value == "None"
            ):
                resolved_default_python_value = None

            # Determine final field type for TypedValue, preferring schema's declared type for static defaults
            final_field_type_for_default = declared_field_type
            if (
                is_default_expr_dynamic
            ):  # If default was an S-expr, re-infer from its resolved value
                final_field_type_for_default = infer_type(resolved_default_python_value)
                # Keep declared type if it's a special case like DATETIME/ENTITY_REF and value is None
                if (
                    declared_field_type in (FieldType.DATETIME, FieldType.ENTITY_REFERENCE)
                    and resolved_default_python_value is None
                ):
                    final_field_type_for_default = declared_field_type

            item_type_hy_obj = get_from_hy_dict(attr_schema_details, "item_type")
            item_type_str = hy_to_python(item_type_hy_obj) # This will be None if item_type wasn't found

            final_attributes_for_model[schema_attr_name] = TypedValue(
                value=resolved_default_python_value,
                field_type=final_field_type_for_default,
                is_dynamic=is_default_expr_dynamic,
                original=original_for_default_tv,
                item_type=(FieldType.from_string(item_type_str) if item_type_str else None), # Use the safe value
                enum_choices=hy_to_python(get_from_hy_dict(attr_schema_details, "enum_choices")),
                item_schema_type=hy_to_python(get_from_hy_dict(attr_schema_details, "item_schema_type")),
                referenced_entity_type=hy_to_python(get_from_hy_dict(attr_schema_details, "referenced_entity_type")),
                referenced_entity_category=hy_to_python(get_from_hy_dict(attr_schema_details, "referenced_entity_category")),
            )

            current_entity_py_attributes_for_self[schema_attr_name] = resolved_default_python_value
            setattr(self_object_for_eval, schema_attr_name, resolved_default_python_value)
            self.logger.debug(
                f"  Applied default for '{schema_attr_name}'. Final TypedValue: {repr(final_attributes_for_model[schema_attr_name])}"
            )

        existing_entity = self._manager.get_by_name_type_category(
            name=entity_instance_name,
            entity_type=entity_type_name_str,
            category=category_name_str,
        )

        if existing_entity:
            # If it exists, update its attributes instead of crashing.
            self.logger.debug(f"Entity '{definition_processing_key}' exists, updating attributes.")
            for attr_name, typed_value in final_attributes_for_model.items():
                existing_entity.set_attribute_typed(attr_name, typed_value)
            return existing_entity
        else:
            # If it does not exist, create it as before.
            self.logger.debug(f"Entity '{definition_processing_key}' not found, creating new.")
            return self._manager.create(
                name=entity_instance_name,
                entity_type=entity_type_name_str,
                category=category_name_str,
                attributes=final_attributes_for_model,
            )

    def process(self, nodes: List[HyNode], context: LoaderContext) -> Dict[str, Entity]:
        self.logger.debug(
            f"EntityLoader.process started. Context type: '{context.current_entity_type}', category: '{context.current_category}'"
        )
        self.context = context
        if not hasattr(context, "variables") or context.variables is None:
            context.variables = {}  # Should be initialized by LoaderContext itself ideally

        definitions_by_processing_key = self.parse_definitions(nodes)
        self.logger.debug(
            f"Parsed entity instance definitions: {list(definitions_by_processing_key.keys())}"
        )
        created_objects: Dict[str, Entity] = {}

        for processing_key, properties_for_creation in definitions_by_processing_key.items():
            try:
                entity_model_instance = self.create_object(processing_key, properties_for_creation)
                created_objects[processing_key] = entity_model_instance
            except Exception as e:
                self.logger.error(
                    f"Error creating/processing entity for key '{processing_key}': {e}",
                    exc_info=True,
                )
                raise
        self.logger.debug(
            f"EntityLoader processing finished for {context.current_entity_type if context else 'N/A'}:{context.current_category if context else 'N/A'}. "
            f"{len(created_objects)} instances."
        )
        return created_objects
