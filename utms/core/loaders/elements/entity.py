from types import SimpleNamespace
from typing import Any, Dict, List, Optional, TYPE_CHECKING

import hy
from hy.models import Expression, Symbol

from utms.core.hy.resolvers.elements.entity import EntityResolver
from utms.core.hy.utils import is_dynamic_content, get_from_hy_dict
from utms.core.loaders.base import ComponentLoader, LoaderContext
from utms.core.managers.elements.entity import EntityManager
from utms.core.models.elements.entity import Entity
from utms.core.services.dynamic import DynamicResolutionService, dynamic_resolution_service
from utms.utils import py_list_to_hy_expression, list_to_dict
from utms.core.hy.converter import converter
from utms.utms_types import HyNode
from utms.utms_types.field.types import FieldType, TypedValue, infer_type

if TYPE_CHECKING:
    from utms.core.components.elements.entity import EntityComponent

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
    def __init__(self, manager: EntityManager, component: 'EntityComponent'):
        super().__init__(manager)
        self.component = component
        self._resolver = EntityResolver(entity_manager=self._manager, component=component)
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

        for raw_attr_name, initial_typed_value in initial_attributes_typed.items():
            attr_name = str(raw_attr_name).replace('-', '_')

            is_complex_list = (
                initial_typed_value.field_type == FieldType.LIST and
                initial_typed_value.item_schema_type and
                isinstance(initial_typed_value.value, list)
            )

            if is_complex_list:
                self.logger.debug(f"  Processing complex list attribute '{attr_name}'...")
                evaluated_list_items = []
                for item in initial_typed_value.value:
                    if not isinstance(item, hy.models.Object):
                        evaluated_list_items.append(item)
                        continue

                    item_plist = converter.model_to_py(item, raw=True)
                    item_dict = list_to_dict(item_plist)

                    evaluated_item_dict = {}
                    for key, val in item_dict.items():
                        is_evaluatable = isinstance(val, list) and len(val) > 0 and val[0] in ['datetime', 'current-time']

                        if is_evaluatable:

                            hy_expr_to_eval = py_list_to_hy_expression(val)
                            resolved_val, _ = self._dynamic_service.evaluate(
                                expression=hy_expr_to_eval,
                                context={"self": self_object_for_eval, **global_variables_for_evaluation},
                                component_type=entity_type_name_str,       
                                component_label=definition_processing_key, 
                                attribute=f"{attr_name}.{key}"             
                            )
                            evaluated_item_dict[key] = resolved_val
                        else:
                            evaluated_item_dict[key] = val

                    evaluated_list_items.append(evaluated_item_dict)

                final_attributes_for_model[attr_name] = TypedValue(
                    value=evaluated_list_items,
                    field_type=initial_typed_value.field_type,
                    item_schema_type=initial_typed_value.item_schema_type
                )
                attributes_processed_from_instance.add(attr_name)
                continue
            original_str = (initial_typed_value.original or "").strip()
            is_quoted = original_str.startswith("'") or original_str.startswith("(quote")

            if is_quoted:
                self.logger.debug(f"  Preserving quoted attribute '{attr_name}' as-is: {original_str}")
                final_attributes_for_model[attr_name] = initial_typed_value

            elif initial_typed_value.is_dynamic:
                self.logger.debug(f"  Evaluating dynamic attribute '{attr_name}': {original_str}")
                resolved_python_value, _ = self._dynamic_service.evaluate(
                    expression=initial_typed_value.value,
                    context={"self": self_object_for_eval, **global_variables_for_evaluation},
                    component_type="entity_attribute",
                    component_label=definition_processing_key,
                    attribute=attr_name
                )
                final_tv_props = initial_typed_value.serialize()
                final_tv_props['value'] = resolved_python_value
                final_attributes_for_model[attr_name] = TypedValue.deserialize(final_tv_props)

            else:
                final_attributes_for_model[attr_name] = initial_typed_value

            attributes_processed_from_instance.add(attr_name)


        for raw_schema_attr_name, attr_schema_details in entity_schema.items():
            schema_attr_name = str(raw_schema_attr_name).replace('-','_')
            if schema_attr_name in attributes_processed_from_instance:
                continue

            default_value_from_schema_hy_obj = get_from_hy_dict(attr_schema_details, "default_value")
            default_value_from_schema = converter.model_to_py(default_value_from_schema_hy_obj, raw=True)

            if get_from_hy_dict(attr_schema_details, "default_value") is None:
                required_hy_obj = get_from_hy_dict(attr_schema_details, "required")
                if converter.model_to_py(required_hy_obj, raw=True) == True:
                    self.logger.error(
                        f"Missing required attribute '{schema_attr_name}' for '{definition_processing_key}' and no default provided."
                    )
                continue
            declared_field_type_str = converter.model_to_py(get_from_hy_dict(attr_schema_details, "type", "string"), raw=True)
            declared_field_type = FieldType.from_string(declared_field_type_str)

            parsed_default_for_tv: Any
            is_default_expr_dynamic = False

            original_for_default_tv: Optional[str] = None

            if isinstance(
                default_value_from_schema, str
            ) and default_value_from_schema.strip().startswith("("):
                parsed_default_for_tv = hy.read(default_value_from_schema.strip())
                is_default_expr_dynamic = is_dynamic_content(parsed_default_for_tv)
            elif isinstance(default_value_from_schema, list):
                try:
                    potential_hy_expr = py_list_to_hy_expression(default_value_from_schema)
                    if is_dynamic_content(potential_hy_expr):
                        parsed_default_for_tv = potential_hy_expr
                        is_default_expr_dynamic = True
                        original_for_default_tv = hy.repr(parsed_default_for_tv)
                    else:
                        parsed_default_for_tv = default_value_from_schema
                        is_default_expr_dynamic = False
                except Exception as e_rebuild:
                    self.logger.error(
                        f"Could not rebuild HyExpr from list for default '{schema_attr_name}': {e_rebuild}. Treating as literal list."
                    )
                    parsed_default_for_tv = default_value_from_schema
                    is_default_expr_dynamic = False
            else:
                parsed_default_for_tv = default_value_from_schema
                is_default_expr_dynamic = False

            resolved_default_python_value: Any
            if is_default_expr_dynamic:
                resolved_default_python_value = None 
            else:
                resolved_default_python_value = parsed_default_for_tv

            if (
                declared_field_type in (FieldType.DATETIME, FieldType.ENTITY_REFERENCE)
                and resolved_default_python_value == "None"
            ):
                resolved_default_python_value = None

            final_field_type_for_default = declared_field_type
            self.logger.debug(
                f"  For default attribute '{schema_attr_name}', using DECLARED schema type: '{final_field_type_for_default}'"
            )

            item_type_hy_obj = get_from_hy_dict(attr_schema_details, "item_type")
            item_type_str = converter.model_to_py(item_type_hy_obj, raw=True)

            final_attributes_for_model[schema_attr_name] = TypedValue(
                value=resolved_default_python_value,
                field_type=final_field_type_for_default,
                is_dynamic=is_default_expr_dynamic,
                original=original_for_default_tv,
                item_type=(FieldType.from_string(item_type_str) if item_type_str else None),
                enum_choices=converter.model_to_py(get_from_hy_dict(attr_schema_details, "enum_choices"), raw=True),
                item_schema_type=converter.model_to_py(get_from_hy_dict(attr_schema_details, "item_schema_type"), raw=True),
                referenced_entity_type=converter.model_to_py(get_from_hy_dict(attr_schema_details, "referenced_entity_type"), raw=True),
                referenced_entity_category=converter.model_to_py(get_from_hy_dict(attr_schema_details, "referenced_entity_category"), raw=True),
            )

            current_entity_py_attributes_for_self[schema_attr_name] = resolved_default_python_value
            setattr(self_object_for_eval, schema_attr_name, resolved_default_python_value)
            self.logger.debug(
                f"  Applied default for '{schema_attr_name}'. Final TypedValue: {repr(final_attributes_for_model[schema_attr_name])}"
            )
        source_filepath = getattr(self.context, 'source_file', None)

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
            existing_entity.source_file = source_filepath
            return existing_entity
        else:
            # If it does not exist, create it as before.
            self.logger.debug(f"Entity '{definition_processing_key}' not found, creating new.")
            return self._manager.create(
                name=entity_instance_name,
                entity_type=entity_type_name_str,
                category=category_name_str,
                attributes=final_attributes_for_model,
                source_file=source_filepath,
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
