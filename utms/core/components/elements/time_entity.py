# utms.core.components.elements.time_entity.py
import os
import shutil
from typing import Any, Dict, List, Optional, Union

import hy
import hy.models

from utms.core.components.base import SystemComponent
from utms.core.hy.ast import HyAST
from utms.core.loaders.base import LoaderContext
from utms.core.loaders.elements.time_entity import TimeEntityLoader
from utms.core.managers.elements.time_entity import TimeEntityManager
from utms.core.models.elements.time_entity import TimeEntity
from utms.core.plugins import plugin_registry
from utms.core.plugins.elements.dynamic_time_entity import plugin_generator
from utms.utils import hy_to_python, list_to_dict, sanitize_filename
from utms.utms_types import HyNode
from utms.utms_types.field.types import FieldType, TypedValue, infer_type


class TimeEntityComponent(SystemComponent):
    """Component managing UTMS time entities with TypedValue attributes and categories."""

    DEFAULT_CATEGORY_FILENAME = "default.hy"
    ENTITY_TYPES_FILENAME = "entity_types.hy"

    def __init__(self, config_dir: str, component_manager=None):
        super().__init__(config_dir, component_manager)
        self._ast_manager = HyAST()
        self._time_entity_manager = TimeEntityManager()
        self._loader = TimeEntityLoader(self._time_entity_manager)
        self._schema_def_dir = os.path.join(self._config_dir, "entities")
        self._entity_type_instances_base_dir = self._config_dir
        self.entity_types: Dict[str, Dict[str, Any]] = {}
        # self._items directly references the manager's items for a single source of truth
        self._items: Dict[str, TimeEntity] = self._time_entity_manager._items

    def _ensure_dirs(self):
        # ... (same as response #15)
        if not os.path.exists(self._schema_def_dir):
            os.makedirs(self._schema_def_dir)
        if not os.path.exists(self._entity_type_instances_base_dir):
            os.makedirs(self._entity_type_instances_base_dir)
        for type_key in self.entity_types.keys():
            type_dir = os.path.join(self._entity_type_instances_base_dir, f"{type_key}s")
            if not os.path.exists(type_dir):
                os.makedirs(type_dir)

    def load(self) -> None:
        # ... (same as response #15, with corrected var_model.value access)
        if self._loaded:
            self.logger.debug("TimeEntityComponent already loaded.")
            return
        self.logger.info("Loading Time Entities...")
        self._time_entity_manager.clear()
        self.entity_types = {}
        self._ensure_dirs()
        try:
            variables_component = self.get_component("variables")
            variables = {}
            if variables_component:
                for name, var_model in variables_component.items():
                    try:
                        var_typed_value = getattr(
                            var_model, "value", var_model
                        )  # Get attribute 'value' if exists
                        py_val = (
                            var_typed_value.value
                            if isinstance(var_typed_value, TypedValue)
                            else hy_to_python(var_typed_value)
                        )
                        variables[name] = py_val
                        variables[name.replace("-", "_")] = py_val
                    except Exception as e:
                        self.logger.error(f"Error processing variable '{name}': {e}", exc_info=True)
            self.logger.debug(f"Context variables for entity loading: {list(variables.keys())}")
            context = LoaderContext(
                config_dir=self._entity_type_instances_base_dir, variables=variables
            )
            entity_types_filepath = os.path.join(self._schema_def_dir, self.ENTITY_TYPES_FILENAME)
            if os.path.exists(entity_types_filepath):
                type_def_nodes = self._ast_manager.parse_file(entity_types_filepath)
                self._extract_entity_types_from_nodes(type_def_nodes)
            else:
                self.logger.warning(
                    f"Entity types definition file not found: {entity_types_filepath}"
                )
            if self.entity_types:
                self._register_entity_type_plugins()
                self._ensure_dirs()
                self._load_entities_from_all_category_files(context)
            else:
                self.logger.info("No entity types defined. Skipping instance loading.")
            self._loaded = True
            self.logger.info(
                f"Time Entities loading complete. Loaded {len(self._items)} instances."
            )
        except Exception as e:
            self.logger.error(f"Fatal error during TimeEntityComponent load: {e}", exc_info=True)
            self._loaded = False
            raise

    def _extract_entity_types_from_nodes(self, type_def_nodes: List[HyNode]) -> None:
        # ... (same as response #15)
        self.entity_types = {}
        for node in type_def_nodes:
            if node.type != "def-time-entity":
                continue
            display_name = str(node.value)
            definition_kind = getattr(node, "definition_kind", None)
            if definition_kind != "entity-type":
                continue
            entity_type_key = display_name.lower()
            raw_hy_attr_schemas: Dict[str, hy.models.HyObject] = getattr(
                node, "attribute_schemas_raw_hy", {}
            )
            processed_py_attr_schemas: Dict[str, Dict[str, Any]] = {}
            for attr_name_str, attr_schema_hy_dict in raw_hy_attr_schemas.items():
                if not isinstance(attr_schema_hy_dict, hy.models.Dict):
                    continue
                try:
                    py_schema_list_of_pairs = hy_to_python(attr_schema_hy_dict)
                    py_schema_dict = list_to_dict(py_schema_list_of_pairs)
                    processed_py_attr_schemas[attr_name_str] = {
                        str(k): v for k, v in py_schema_dict.items()
                    }
                except Exception as e_conv:
                    self.logger.error(
                        f"Error converting schema for '{attr_name_str}' of '{display_name}': {e_conv}",
                        exc_info=True,
                    )
            self.entity_types[entity_type_key] = {
                "name": display_name,
                "attributes_schema": processed_py_attr_schemas,
            }
            self.logger.info(f"Extracted schema for entity type '{entity_type_key}'")

    def _register_entity_type_plugins(self) -> None:
        # ... (same as response #15)
        if not self.entity_types:
            return
        for entity_type_key, schema_definition in self.entity_types.items():
            try:
                plugin_class = plugin_generator.generate_plugin(
                    entity_type_key, schema_definition.get("attributes_schema", {})
                )
                plugin_registry.register_node_plugin(plugin_class)
                self.logger.debug(
                    f"Registered plugin '{plugin_class.__name__}' for 'def-{entity_type_key}'."
                )
            except Exception as e:
                self.logger.error(
                    f"Error registering plugin for '{entity_type_key}': {e}", exc_info=True
                )

    def _load_entities_from_all_category_files(self, context: LoaderContext) -> None:
        # ... (same as response #15)
        total_instances_loaded_all_types = 0
        for entity_type_key in self.entity_types.keys():
            type_specific_instance_dir = os.path.join(
                self._entity_type_instances_base_dir, f"{entity_type_key}s"
            )
            if not os.path.isdir(type_specific_instance_dir):
                continue
            category_files = [
                f for f in os.listdir(type_specific_instance_dir) if f.endswith(".hy")
            ]
            if not category_files:
                continue
            for filename in category_files:
                category_name = sanitize_filename(os.path.splitext(filename)[0])
                filepath = os.path.join(type_specific_instance_dir, filename)
                try:
                    instance_nodes = self._ast_manager.parse_file(filepath)
                    if not instance_nodes:
                        continue
                    category_context = LoaderContext(
                        config_dir=context.config_dir,
                        variables=context.variables,
                        current_category=category_name,
                        current_entity_type=entity_type_key,
                    )
                    loaded_instances = self._loader.process(instance_nodes, category_context)
                    total_instances_loaded_all_types += len(loaded_instances)
                except Exception as e_file:
                    self.logger.error(f"Error loading from '{filepath}': {e_file}", exc_info=True)
        self.logger.debug(
            f"Total instances from category files: {total_instances_loaded_all_types}"
        )

    def save(self) -> None:
        # ... (same as response #15, including debug logs for save)
        self.logger.info("Saving Time Entities...")
        self._ensure_dirs()
        entity_types_filepath = os.path.join(self._schema_def_dir, self.ENTITY_TYPES_FILENAME)
        schema_plugin = plugin_registry.get_node_plugin("def-time-entity")
        if schema_plugin:
            type_def_hy_lines = []
            for entity_type_key in sorted(self.entity_types.keys()):
                schema_def = self.entity_types[entity_type_key]
                display_name = schema_def["name"]
                python_attr_schemas = schema_def["attributes_schema"]
                attr_schemas_for_hy_node: Dict[str, hy.models.HyObject] = {}
                for attr_name, py_schema_dict in python_attr_schemas.items():
                    hy_dict_elements = []
                    for k, v_item in py_schema_dict.items():
                        hy_dict_elements.append(hy.models.Keyword(k))
                        if isinstance(v_item, str):
                            hy_dict_elements.append(hy.models.String(v_item))
                        elif isinstance(v_item, int):
                            hy_dict_elements.append(hy.models.Integer(v_item))
                        elif isinstance(v_item, bool):
                            hy_dict_elements.append(hy.models.Boolean(v_item))
                        elif isinstance(v_item, list):
                            hy_dict_elements.append(
                                hy.models.List([hy.models.String(str(i)) for i in v_item])
                            )
                        else:
                            hy_dict_elements.append(hy.models.String(str(v_item)))
                    attr_schemas_for_hy_node[attr_name] = hy.models.Dict(hy_dict_elements)
                node_for_formatting = HyNode(type="def-time-entity", value=display_name)
                setattr(node_for_formatting, "definition_kind", "entity-type")
                setattr(node_for_formatting, "attribute_schemas_raw_hy", attr_schemas_for_hy_node)
                type_def_hy_lines.extend(schema_plugin.format(node_for_formatting))
                type_def_hy_lines.append("")
            try:
                with open(entity_types_filepath, "w", encoding="utf-8") as f:
                    f.write("\n".join(type_def_hy_lines))
                self.logger.info(
                    f"Saved {len(self.entity_types)} entity type defs to {entity_types_filepath}"
                )
            except Exception as e_save_schema:
                self.logger.error(f"Error saving entity type defs: {e_save_schema}", exc_info=True)
        else:
            self.logger.error("Schema plugin 'def-time-entity' not found. Cannot save schemas.")

        instances_by_type_and_category: Dict[str, Dict[str, List[TimeEntity]]] = {}
        for entity_instance in self._items.values():
            instances_by_type_and_category.setdefault(entity_instance.entity_type, {}).setdefault(
                entity_instance.category, []
            ).append(entity_instance)

        existing_files_to_check_for_emptiness = {}
        for entity_type_key, categories_dict in instances_by_type_and_category.items():
            type_specific_instance_dir = os.path.join(
                self._entity_type_instances_base_dir, f"{entity_type_key}s"
            )
            if not os.path.exists(type_specific_instance_dir):
                os.makedirs(type_specific_instance_dir)
            for f_name in os.listdir(type_specific_instance_dir):
                if f_name.endswith(".hy"):
                    existing_files_to_check_for_emptiness[
                        os.path.join(type_specific_instance_dir, f_name)
                    ] = True
            for category_key, instances_list in categories_dict.items():
                instance_plugin = plugin_registry.get_node_plugin(f"def-{entity_type_key}")
                if not instance_plugin:
                    self.logger.warning(
                        f"No plugin for 'def-{entity_type_key}'. Cannot save for '{entity_type_key}/{category_key}'."
                    )
                    continue
                category_filename = f"{sanitize_filename(category_key)}.hy"
                instance_file_path = os.path.join(type_specific_instance_dir, category_filename)
                instance_hy_lines = []
                for entity_instance in sorted(instances_list, key=lambda inst: inst.name):
                    node_for_formatting = HyNode(
                        type=f"def-{entity_type_key}", value=entity_instance.name
                    )
                    setattr(
                        node_for_formatting,
                        "attributes_typed",
                        entity_instance.get_all_attributes_typed(),
                    )
                    # --- PASTE DEBUG LOGS FROM RESPONSE #15 HERE ---
                    if (
                        entity_instance.name == "Complete UTMS migration"
                        or "test" in entity_instance.name
                    ):
                        self.logger.debug(
                            f"DEBUG SAVE: Entity '{entity_instance.name}' (type: {entity_instance.entity_type})"
                        )
                        for (
                            attr_name_debug,
                            tv_debug,
                        ) in entity_instance.get_all_attributes_typed().items():
                            self.logger.debug(f"  Attr '{attr_name_debug}':")
                            self.logger.debug(
                                f"    tv_debug.value = {repr(tv_debug.value)} (Type: {type(tv_debug.value)})"
                            )
                            self.logger.debug(f"    tv_debug.field_type = {tv_debug.field_type}")
                            self.logger.debug(f"    tv_debug.is_dynamic = {tv_debug.is_dynamic}")
                            self.logger.debug(f"    tv_debug.original = {repr(tv_debug.original)}")
                            persistence_string = tv_debug.serialize_for_persistence()
                            self.logger.debug(
                                f"    serialize_for_persistence() -> {repr(persistence_string)}"
                            )
                            if (
                                tv_debug.is_dynamic
                                and tv_debug.original
                                and persistence_string != tv_debug.original
                            ):
                                self.logger.error(
                                    f"PERSISTENCE MISMATCH for dynamic '{attr_name_debug}': Original='{tv_debug.original}', Got='{persistence_string}'"
                                )
                            elif (
                                not tv_debug.is_dynamic
                                and isinstance(tv_debug.value, str)
                                and tv_debug.value.startswith("{'value':")
                            ):  # Heuristic
                                self.logger.error(
                                    f"PERSISTENCE LOOKS LIKE SERIALIZED DICT for static '{attr_name_debug}': {persistence_string}"
                                )
                    # --- END DEBUG AREA ---
                    instance_hy_lines.extend(instance_plugin.format(node_for_formatting))
                    instance_hy_lines.append("")
                try:
                    with open(instance_file_path, "w", encoding="utf-8") as f:
                        f.write("\n".join(instance_hy_lines))
                    self.logger.info(
                        f"Saved {len(instances_list)} of '{entity_type_key}' (cat: '{category_key}') to {instance_file_path}"
                    )
                    if instance_file_path in existing_files_to_check_for_emptiness:
                        del existing_files_to_check_for_emptiness[instance_file_path]
                except Exception as e_save_inst:
                    self.logger.error(
                        f"Error saving '{entity_type_key}/{category_key}': {e_save_inst}",
                        exc_info=True,
                    )
        for empty_filepath in existing_files_to_check_for_emptiness.keys():
            if os.path.basename(empty_filepath).lower() != self.DEFAULT_CATEGORY_FILENAME.lower():
                try:
                    os.remove(empty_filepath)
                    self.logger.info(f"Removed empty category file: {empty_filepath}")
                except OSError as e_remove:
                    self.logger.error(f"Error removing {empty_filepath}: {e_remove}")
        self.logger.info("Time Entities saving complete.")

    def _get_entity_schema(self, entity_type_str: str) -> Optional[Dict[str, Any]]:
        # ... (same as response #15) ...
        type_def = self.entity_types.get(entity_type_str.lower())
        return type_def.get("attributes_schema") if type_def else None

    # --- ADDED/RESTORED GETTER METHODS ---
    def get_entity(self, entity_type: str, name: str) -> Optional[TimeEntity]:
        """
        Get a specific entity by type and name.
        Assumes entity names are unique across all categories for a given type.
        If names are unique only within a category, this method needs a 'category' param.
        """
        # The manager's get_by_name_and_type already uses the key "entity_type:name"
        return self._time_entity_manager.get_by_name_and_type(name, entity_type.lower())

    def get_by_type(self, entity_type: str, category: Optional[str] = None) -> List[TimeEntity]:
        """
        Get all entities of a specific type, optionally filtered by category.
        """
        # The manager's get_by_type now handles category filtering.
        return self._time_entity_manager.get_by_type(entity_type.lower(), category)

    def get_entity_types(self) -> List[str]:
        """
        Get all registered entity type keys (lowercase strings like "task", "event").
        """
        if not self.entity_types and not self._loaded:
            self.logger.debug("Entity types not determined yet. Calling self.load().")
            self.load()
        elif not self.entity_types and self._loaded:
            self.logger.warning("Component loaded but no entity types found.")
        return list(self.entity_types.keys())  # Keys of self.entity_types are lowercase

    def get_all_entity_type_details(self) -> List[Dict[str, Any]]:
        # ... (same as response #15) ...
        if not self._loaded:
            self.load()
        details = []
        for type_key_lower, type_data_dict in self.entity_types.items():
            details.append(
                {
                    "name": type_key_lower,
                    "displayName": type_data_dict.get("name", type_key_lower.upper()),
                    "attributes": type_data_dict.get("attributes_schema", {}),
                }
            )
        return details

    # --- CRUD methods using manager and TypedValues ---
    def create_entity(
        self,
        name: str,
        entity_type: str,
        attributes_raw: Optional[Dict[str, Any]] = None,
        category: str = "default",  # Added category parameter
    ) -> TimeEntity:
        # ... (This is the corrected version from response #15, including resolution)
        self.logger.debug(
            f"Component.create_entity: name='{name}', type='{entity_type}', category='{category}', raw_attrs='{attributes_raw}'"
        )
        entity_type_key = entity_type.lower()
        category_key = sanitize_filename(
            category.strip().lower() if category and category.strip() else "default"
        )
        schema = self._get_entity_schema(entity_type_key) or {}
        final_typed_attributes: Dict[str, TypedValue] = {}
        raw_attributes_to_process = attributes_raw or {}
        variables_for_eval_context = {}
        variables_component = self.get_component("variables")
        if variables_component:
            for var_name_ctx, var_model_ctx in variables_component.items():
                val_to_add = getattr(
                    var_model_ctx.value, "value", getattr(var_model_ctx, "value", None)
                )
                if val_to_add is not None:
                    variables_for_eval_context[var_name_ctx] = val_to_add
                    variables_for_eval_context[var_name_ctx.replace("-", "_")] = val_to_add
        for attr_name, raw_value_from_api in raw_attributes_to_process.items():
            attr_schema_details = schema.get(attr_name, {})
            declared_type_str = attr_schema_details.get("type")
            field_type_enum = (
                FieldType.from_string(declared_type_str)
                if declared_type_str
                else infer_type(raw_value_from_api)
            )
            item_type_str = attr_schema_details.get("item_type")
            item_type_enum = FieldType.from_string(item_type_str) if item_type_str else None
            enum_choices = attr_schema_details.get("enum_choices", [])
            is_dynamic = False
            original_expr = None
            value_for_typed_value_constructor = raw_value_from_api
            if (
                isinstance(raw_value_from_api, str)
                and raw_value_from_api.strip().startswith("(")
                and raw_value_from_api.strip().endswith(")")
            ):
                is_dynamic = True
                original_expr = raw_value_from_api
                if field_type_enum != FieldType.CODE:
                    try:
                        resolved_val_raw, _ = self._loader._dynamic_service.evaluate(
                            expression=original_expr,
                            context=variables_for_eval_context,
                            component_type=f"time_entity.{entity_type_key}",
                            component_label=name,
                            attribute=attr_name,
                        )
                        value_for_typed_value_constructor = hy_to_python(resolved_val_raw)
                    except Exception as e_resolve:
                        self.logger.error(
                            f"Resolve fail in create for '{attr_name}': {e_resolve}. Storing original as value for CODE or None.",
                            exc_info=True,
                        )
                        value_for_typed_value_constructor = (
                            original_expr if field_type_enum == FieldType.CODE else None
                        )
            final_typed_attributes[attr_name] = TypedValue(
                value=value_for_typed_value_constructor,
                field_type=field_type_enum,
                is_dynamic=is_dynamic,
                original=original_expr,
                enum_choices=enum_choices,
                item_type=item_type_enum,
            )
            for attr_name_check, tv_check in final_typed_attributes.items():
                attr_schema_detail = schema.get(attr_name_check, {})
                if attr_schema_detail.get("required"):  # Check if schema declared it as required
                    val_to_check = tv_check.value
                    is_empty = False
                    if val_to_check is None:
                        is_empty = True
                    elif isinstance(val_to_check, str) and not val_to_check.strip():
                        is_empty = True
                    elif isinstance(val_to_check, list) and not val_to_check:  # Empty list
                        is_empty = True
                    # Add other checks for emptiness based on type if needed

                    if is_empty:
                        error_msg = f"Attribute '{attr_name_check}' is required for entity type '{entity_type_key}' but was empty or not provided."
                        self.logger.warning(error_msg)
                        raise ValueError(error_msg)

        entity_instance = self._time_entity_manager.create(
            name=name,
            entity_type=entity_type_key,
            attributes=final_typed_attributes,
            category=category_key,
        )
        self.save()
        return entity_instance

    def update_entity_attribute(
        self,
        entity_type: str,
        name: str,
        attr_name: str,
        new_raw_value_from_api: Any,
        is_new_value_dynamic: bool = False,
        new_original_expression: Optional[str] = None,
    ):
        # ... (This is the corrected version from response #15, including resolution)
        entity = self.get_entity(entity_type, name)
        if not entity:
            raise ValueError(f"Entity {entity_type}:{name} not found for update.")
        existing_typed_value = entity.get_attribute_typed(attr_name)
        schema = self._get_entity_schema(entity_type.lower()) or {}
        attr_schema_details = schema.get(attr_name, {})
        field_type_for_new_tv: FieldType
        declared_type_str = attr_schema_details.get("type")
        if existing_typed_value:
            field_type_for_new_tv = existing_typed_value.field_type
        elif declared_type_str:
            field_type_for_new_tv = FieldType.from_string(declared_type_str)
        else:
            field_type_for_new_tv = infer_type(new_raw_value_from_api)
        item_type_str = attr_schema_details.get("item_type")
        item_type_enum = (
            FieldType.from_string(item_type_str)
            if item_type_str
            else (existing_typed_value.item_type if existing_typed_value else None)
        )
        enum_choices = attr_schema_details.get("enum_choices", [])
        if not enum_choices and existing_typed_value and existing_typed_value.enum_choices:
            enum_choices = existing_typed_value.enum_choices
        value_to_store_in_typed_value = new_raw_value_from_api
        if is_new_value_dynamic:
            if not new_original_expression or not new_original_expression.strip().startswith("("):
                raise ValueError(
                    "Dynamic update requires valid Hy s-expression for 'new_original_expression'."
                )
            variables_for_eval_context = {}
            variables_component = self.get_component("variables")
            if variables_component:
                for var_n, var_m in variables_component.items():
                    variables_for_eval_context[var_n] = getattr(
                        var_m.value, "value", None
                    )  # Simplified
            try:
                resolved_val_raw, _ = self._loader._dynamic_service.evaluate(
                    expression=new_original_expression,
                    context=variables_for_eval_context,
                    component_type=f"time_entity.{entity_type.lower()}",
                    component_label=name,
                    attribute=attr_name,
                )
                value_to_store_in_typed_value = hy_to_python(resolved_val_raw)
                if field_type_for_new_tv == FieldType.CODE and not isinstance(
                    value_to_store_in_typed_value, str
                ):
                    field_type_for_new_tv = infer_type(value_to_store_in_typed_value)
            except Exception as e_resolve:
                self.logger.error(
                    f"Failed to resolve expr '{new_original_expression}' for update: {e_resolve}. Storing original or None.",
                    exc_info=True,
                )
                value_to_store_in_typed_value = (
                    new_original_expression if field_type_for_new_tv == FieldType.CODE else None
                )
            updated_typed_value = TypedValue(
                value=value_to_store_in_typed_value,
                field_type=field_type_for_new_tv,
                is_dynamic=True,
                original=new_original_expression,
                enum_choices=enum_choices,
                item_type=item_type_enum,
            )
        else:
            updated_typed_value = TypedValue(
                value=new_raw_value_from_api,
                field_type=field_type_for_new_tv,
                is_dynamic=False,
                original=None,
                enum_choices=enum_choices,
                item_type=item_type_enum,
            )
        entity.set_attribute_typed(attr_name, updated_typed_value)
        self.save()
        self.logger.info(
            f"Updated attribute '{attr_name}' for entity '{entity_type}:{name}'. New TV: {repr(updated_typed_value)}"
        )

    def remove_entity(self, entity_type: str, name: str) -> None:
        # ... (same as response #15)
        key = f"{entity_type.lower()}:{name}"
        if key in self._items:
            self._time_entity_manager.remove(key)
            self.save()
        else:
            self.logger.warning(
                f"Entity not found for removal: type='{entity_type}', name='{name}'"
            )

    def rename_entity(self, entity_type: str, old_name: str, new_name: str) -> None:
        # ... (same as response #15)
        entity_type_key = entity_type.lower()
        old_internal_key = f"{entity_type_key}:{old_name}"
        new_internal_key = f"{entity_type_key}:{new_name}"
        if old_internal_key not in self._items:
            raise ValueError(f"Entity to rename not found: {old_internal_key}")
        if new_internal_key in self._items:
            raise ValueError(f"New entity name already exists: {new_internal_key}")
        entity_to_rename = self._items.pop(old_internal_key)
        original_category = entity_to_rename.category
        entity_to_rename.name = new_name
        self._items[new_internal_key] = entity_to_rename
        self.save()
        self.logger.info(
            f"Renamed entity from '{old_internal_key}' to '{new_internal_key}' (category: '{original_category}')."
        )

    # --- Category Management Methods ---
    def get_categories(self, entity_type_str: str) -> List[str]:
        # ... (same as response #15)
        entity_type_key = entity_type_str.lower()
        type_specific_dir = os.path.join(
            self._entity_type_instances_base_dir, f"{entity_type_key}s"
        )
        categories = []
        if os.path.isdir(type_specific_dir):
            for filename in os.listdir(type_specific_dir):
                if filename.endswith(".hy"):
                    categories.append(sanitize_filename(os.path.splitext(filename)[0]))
        return sorted(
            list(set(c for c in categories if c))
        )  # Filter out empty strings from sanitize

    def create_category(self, entity_type_str: str, category_name: str) -> bool:
        # ... (same as response #15)
        entity_type_key = entity_type_str.lower()
        category_filename_part = sanitize_filename(category_name.lower())
        if not category_filename_part:
            raise ValueError("Category name invalid.")
        type_specific_dir = os.path.join(
            self._entity_type_instances_base_dir, f"{entity_type_key}s"
        )
        if not os.path.exists(type_specific_dir):
            os.makedirs(type_specific_dir)
        category_filepath = os.path.join(type_specific_dir, f"{category_filename_part}.hy")
        if os.path.exists(category_filepath):
            self.logger.warning(f"Category file '{category_filepath}' already exists.")
            return False
        try:
            with open(category_filepath, "w", encoding="utf-8") as f:
                f.write(f";; Category: {category_name}\n")
            self.logger.info(f"Created category file {category_filepath}.")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create {category_filepath}: {e}", exc_info=True)
            return False

    def rename_category(
        self, entity_type_str: str, old_category_name: str, new_category_name: str
    ) -> bool:
        # ... (same as response #15)
        entity_type_key = entity_type_str.lower()
        old_cat_fn_part = sanitize_filename(old_category_name.lower())
        new_cat_fn_part = sanitize_filename(new_category_name.lower())
        if not old_cat_fn_part or not new_cat_fn_part or old_cat_fn_part == new_cat_fn_part:
            raise ValueError("Invalid category names for rename.")
        type_specific_dir = os.path.join(
            self._entity_type_instances_base_dir, f"{entity_type_key}s"
        )
        old_filepath = os.path.join(type_specific_dir, f"{old_cat_fn_part}.hy")
        new_filepath = os.path.join(type_specific_dir, f"{new_cat_fn_part}.hy")
        if not os.path.exists(old_filepath):
            self.logger.warning(f"Category to rename '{old_filepath}' not found.")
            return False
        if os.path.exists(new_filepath):
            self.logger.warning(f"New category name '{new_filepath}' already exists.")
            return False
        entities_to_update = [
            e
            for e in self._items.values()
            if e.entity_type == entity_type_key and e.category == old_cat_fn_part
        ]
        try:
            shutil.move(old_filepath, new_filepath)
            for entity in entities_to_update:
                entity.category = new_cat_fn_part
            self.logger.info(
                f"Renamed category '{old_filepath}' to '{new_filepath}'. Updated {len(entities_to_update)} entities in memory."
            )
            # self.save() # Consider if immediate save is needed or if next global save is enough
            return True
        except Exception as e:
            self.logger.error(f"Error renaming category: {e}", exc_info=True)
            return False

    def delete_category(
        self, entity_type_str: str, category_name: str, move_entities_to_default: bool = True
    ) -> bool:
        # ... (same as response #15)
        entity_type_key = entity_type_str.lower()
        category_to_delete_fn_part = sanitize_filename(category_name.lower())
        if not category_to_delete_fn_part or category_to_delete_fn_part == "default":
            self.logger.error(f"Cannot delete invalid/default category: '{category_name}'.")
            return False
        type_specific_dir = os.path.join(
            self._entity_type_instances_base_dir, f"{entity_type_key}s"
        )
        category_filepath = os.path.join(type_specific_dir, f"{category_to_delete_fn_part}.hy")
        if not os.path.exists(category_filepath):
            self.logger.warning(f"Category to delete '{category_filepath}' not found.")
            return True  # Idempotent
        entities_in_category = [
            e
            for e in self._items.values()
            if e.entity_type == entity_type_key and e.category == category_to_delete_fn_part
        ]
        try:
            os.remove(category_filepath)
            self.logger.info(f"Deleted category file: {category_filepath}")
            if move_entities_to_default:
                for entity in entities_in_category:
                    entity.category = "default"
                self.logger.info(
                    f"Moved {len(entities_in_category)} entities from '{category_name}' to 'default' in memory."
                )
            else:
                for entity in entities_in_category:
                    if f"{entity.entity_type}:{entity.name}" in self._items:
                        del self._items[f"{entity.entity_type}:{entity.name}"]
                self.logger.info(
                    f"Deleted {len(entities_in_category)} entities from category '{category_name}'."
                )
            # self.save() # Consider if immediate save is needed
            return True
        except Exception as e:
            self.logger.error(f"Error deleting category '{category_name}': {e}", exc_info=True)
            return False

    def move_entity_to_category(
        self, entity_type: str, entity_name: str, new_category_name: str
    ) -> bool:
        # ... (same as response #15)
        entity = self.get_entity(entity_type, entity_name)
        if not entity:
            self.logger.error(f"Entity '{entity_type}:{entity_name}' not found to move.")
            return False
        new_cat_key = sanitize_filename(
            new_category_name.lower()
            if new_category_name and new_category_name.strip()
            else "default"
        )
        entity.category = new_cat_key
        self.logger.info(
            f"Entity '{entity_type}:{entity_name}' category set to '{new_cat_key}' in memory."
        )
        self.save()
        return True

    def get_tasks(self, category: Optional[str] = None) -> List[TimeEntity]:
        return self.get_by_type("task", category)

    # ... other convenience getters for specific types
