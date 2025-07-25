from typing import Any, Dict, List, Optional, Type

import hy

from utms.core.hy.utils import hy_obj_to_string, is_dynamic_content, get_from_hy_dict, python_to_hy_string
from utms.core.mixins.base import LoggerMixin
from utms.core.plugins import NodePlugin
from utms.utms_types import HyNode
# Import TypedValue and FieldType related items
from utms.utms_types.field.types import FieldType, TypedValue, infer_type
from utms.utils import hy_to_python


class DynamicEntityPlugin(NodePlugin, LoggerMixin):
    """
    Base class for dynamically generated plugins that parse specific entity instances
    (e.g., a (def-task ...) form).
    An instance of a generated subclass (e.g., TaskInstanceParserPlugin) is created for each defined entity type.
    """

    __discoverable__ = False  # This base class itself is not discovered.

    def __init__(self, entity_type_str: str, attribute_schemas: Dict[str, Dict[str, Any]]):
        """
        Constructor for the base or generated plugin.
        :param entity_type_str: The lowercase string name of the entity type (e.g., "task").
        :param attribute_schemas: The schema for attributes of this entity type,
                                  e.g., {'description': {'type': 'string', 'label': 'Desc', ...}, ...}
        """
        self._entity_type_str = entity_type_str
        self._attribute_schemas = (attribute_schemas or {}).copy()

        self.logger.debug(
            f"Initialized DynamicEntityPlugin for type '{self._entity_type_str}' "
            f"(effective node_type: 'def-{self._entity_type_str.lower()}'). "
            f"Attribute schemas: {self._attribute_schemas}"
        )

    @property
    def name(self) -> str:
        return f"{self._entity_type_str.capitalize()} Instance Parser Plugin"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def node_type(self) -> str:
        return f"def-{self._entity_type_str.lower()}"

    def initialize(self, system_context: Dict[str, Any]):
        pass

    def parse(self, expr: hy.models.Expression) -> Optional[HyNode]:
        """
        Parse an entity instance definition (e.g., a (def-task "My Task" (priority 10)) form).
        """
        if not (
            isinstance(expr, hy.models.Expression)
            and len(expr) >= 2
            and str(expr[0]).lower() == self.node_type
        ):
            self.logger.error(
                f"Expression '{expr}' is not a valid '{self.node_type}' definition or is too short."
            )
            return None

        entity_instance_name = str(expr[1])

        self.logger.debug(
            f"Parsing {self.node_type} instance: '{entity_instance_name}' "
            f"using schema for '{self._entity_type_str}'"
        )

        parsed_attributes_typed: Dict[str, TypedValue] = {}

        for attr_expr_in_hy in expr[2:]:
            if not (
                isinstance(attr_expr_in_hy, hy.models.Expression) and len(attr_expr_in_hy) >= 2
            ):
                self.logger.debug(f"  Skipping invalid attribute expression: {attr_expr_in_hy}")
                continue

            attr_name_from_hy = str(attr_expr_in_hy[0])
            raw_hy_value_object = attr_expr_in_hy[1]
            normalized_attr_name_for_schema_lookup = attr_name_from_hy.replace('_', '-')
            self.logger.debug(f"  Attribute from Hy: '{attr_name_from_hy}' = {raw_hy_value_object}")

            attr_schema_details = self._attribute_schemas.get(normalized_attr_name_for_schema_lookup)
            if not attr_schema_details:
                self.logger.warning(
                    f"No schema definition found for attribute '{normalized_attr_name_for_schema_lookup}' "
                    f"in entity type '{self._entity_type_str}' (instance: '{entity_instance_name}'). "
                    f"Will attempt to infer type, but this is not ideal."
                )
                attr_schema_details = hy.models.Dict()

            declared_type_str = hy_to_python(get_from_hy_dict(attr_schema_details, "type"))

            field_type_enum: FieldType
            if declared_type_str:
                field_type_enum = FieldType.from_string(declared_type_str)
            else:
                # Fallback if schema 'type' is missing (should be logged by schema parser ideally)
                self.logger.warning(
                    f"Missing schema 'type' for '{attr_name_from_hy}' in '{self._entity_type_str}'. "
                    f"Inferring type from value: {raw_hy_value_object}"
                )
                field_type_enum = infer_type(raw_hy_value_object)

            item_type_str = hy_to_python(get_from_hy_dict(attr_schema_details, "item_type"))
            item_type_enum = FieldType.from_string(item_type_str) if item_type_str else None
            enum_choices_from_schema = hy_to_python(get_from_hy_dict(attr_schema_details, "enum_choices", default=[]))

            item_schema_type_str = hy_to_python(get_from_hy_dict(attr_schema_details, "item_schema_type"))
            ref_type_from_schema = hy_to_python(get_from_hy_dict(attr_schema_details, "ref-type"))            
            referenced_entity_type_str = ref_type_from_schema
            referenced_entity_category_str = hy_to_python(get_from_hy_dict(attr_schema_details, "referenced_entity_category"))

            is_dynamic_attr = is_dynamic_content(raw_hy_value_object)
            original_expr_str_for_typed_value = None
            if is_dynamic_attr:
                original_expr_str_for_typed_value = hy_obj_to_string(raw_hy_value_object)

            try:
                typed_value_for_attr = TypedValue(
                    value=raw_hy_value_object,
                    field_type=field_type_enum,
                    item_type=item_type_enum,
                    is_dynamic=is_dynamic_attr,
                    original=original_expr_str_for_typed_value,
                    enum_choices=enum_choices_from_schema,
                    item_schema_type=item_schema_type_str,
                    referenced_entity_type=referenced_entity_type_str,
                    referenced_entity_category=referenced_entity_category_str,
                )
                parsed_attributes_typed[attr_name_from_hy] = typed_value_for_attr
            except Exception as e_typed_value:
                self.logger.error(
                    f"Error creating TypedValue for attribute '{attr_name_from_hy}' "
                    f"of entity '{entity_instance_name}' ({self._entity_type_str}): {e_typed_value}",
                    exc_info=True,
                )
                continue

        node = HyNode(
            type=self.node_type, value=entity_instance_name, original=hy_obj_to_string(expr), children=[]
        )
        setattr(node, "attributes_typed", parsed_attributes_typed)
        setattr(node, "entity_type_name_str", self._entity_type_str)  # e.g., "task"

        self.logger.debug(
            f"HyNode for '{entity_instance_name}' ({self.node_type}) parsed with "
            f"{len(parsed_attributes_typed)} initial TypedValue attributes."
        )
        return node

    def format(self, node: HyNode) -> List[str]:
        """Format entity instance definition (HyNode with 'attributes_typed') back to Hy code."""
        value = node.value
        if isinstance(value, hy.models.Object):
            entity_instance_name_str = hy_obj_to_string(value)
        else:
            entity_instance_name_str = python_to_hy_string(value)

        lines = [f"({node.type} {entity_instance_name_str}"]

        attributes_typed_dict: Optional[Dict[str, TypedValue]] = getattr(
            node, "attributes_typed", None
        )

        if attributes_typed_dict:
            sorted_attributes = sorted(
                [(str(k).lstrip(':'), v) for k, v in attributes_typed_dict.items()]
            )
            for attr_name, typed_value_instance in sorted_attributes:
                value_str_for_hy_file = typed_value_instance.serialize_for_persistence()
                lines.append(f"  ({attr_name} {value_str_for_hy_file})")

        lines.append(")")
        return lines


class DynamicEntityPluginGenerator(LoggerMixin):
    """
    Generates specific entity instance parser plugins (e.g., TaskInstanceParserPlugin)
    dynamically based on entity type schema definitions.
    """

    def __init__(self):
        self.registered_plugins: Dict[str, Type[DynamicEntityPlugin]] = (
            {}
        ) 

    def generate_plugin(
        self,
        entity_type_name_str: str,
        attributes_schema_for_type: Dict[str, Any],  
    ) -> Type[DynamicEntityPlugin]:
        """
        Generates and returns a new plugin class tailored for parsing instances of 'entity_type_name_str'.
        """
        self.logger.debug(
            f"Generating instance parser plugin for entity type string: '{entity_type_name_str}'"
        )
        self.logger.debug(
            f"Attribute schema to be used by new plugin: {attributes_schema_for_type}"
        )
        generated_class_name = f"{entity_type_name_str.capitalize()}InstanceParserPlugin"
        def generated_plugin_constructor(self_of_generated_plugin):
            DynamicEntityPlugin.__init__(
                self_of_generated_plugin,
                entity_type_str=entity_type_name_str,  # Pass the specific entity type string
                attribute_schemas=attributes_schema_for_type,  # Pass its specific schema
            )

        GeneratedPluginClass = type(
            generated_class_name, 
            (DynamicEntityPlugin,), 
            {
                "__init__": generated_plugin_constructor,
            },
        )

        self.registered_plugins[entity_type_name_str] = GeneratedPluginClass
        self.logger.info(  # Changed to INFO for successful generation
            f"Successfully created and registered instance parser plugin class: "
            f"'{GeneratedPluginClass.__name__}' for node_type 'def-{entity_type_name_str.lower()}'."
        )
        return GeneratedPluginClass


# Singleton instance of the generator
plugin_generator = DynamicEntityPluginGenerator()
