import os
import shutil
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

import hy
import hy.models
import sh

from utms.core.components.base import SystemComponent
from utms.core.hy.ast import HyAST
from utms.core.loaders.base import LoaderContext
from utms.core.loaders.elements.entity import EntityLoader
from utms.core.managers.elements.entity import EntityManager
from utms.core.models.elements.entity import Entity
from utms.core.plugins import plugin_registry
from utms.core.plugins.elements.dynamic_entity import plugin_generator
from utms.utils import hy_to_python, list_to_dict, sanitize_filename
from utms.utms_types import HyNode
from utms.utms_types.field.types import FieldType, TypedValue, infer_type


class EntityComponent(SystemComponent):
    """Component managing UTMS entities with TypedValue attributes and categories."""

    def __init__(self, config_dir: str, component_manager=None):
        super().__init__(config_dir, component_manager)
        self._ast_manager = HyAST()
        # Use the renamed EntityManager and EntityLoader
        self._entity_manager = EntityManager()
        self._loader = EntityLoader(self._entity_manager)

        self._entity_schema_def_dir = os.path.join(self._config_dir, "entities")
        self._complex_type_def_dir = os.path.join(self._config_dir, "types")

        self._entity_type_instances_base_dir = self._config_dir

        self.entity_types: Dict[str, Dict[str, Any]] = {}
        self.complex_types: Dict[str, Dict[str, Any]] = {}

        self._items: Dict[str, Entity] = self._entity_manager._items

    def _ensure_dirs(self):
        if not os.path.exists(self._config_dir):
            os.makedirs(self._config_dir)

        if not os.path.exists(self._entity_schema_def_dir):
            os.makedirs(self._entity_schema_def_dir)
            self.logger.info(
                f"Created entity schema definition directory: {self._entity_schema_def_dir}"
            )

        if not os.path.exists(self._complex_type_def_dir):
            os.makedirs(self._complex_type_def_dir)
            self.logger.info(
                f"Created complex type definition directory: {self._complex_type_def_dir}"
            )
        if self.entity_types:
            for type_key in self.entity_types.keys():
                type_dir = os.path.join(self._entity_type_instances_base_dir, f"{type_key}s")
                if not os.path.exists(type_dir):
                    os.makedirs(type_dir)

    def load(self) -> None:
        if self._loaded:
            self.logger.debug("EntityComponent already loaded.")
            return
        self.logger.info("Loading Entities...")
        self._entity_manager.clear()

        self.entity_types = {}
        self._ensure_dirs()
        try:
            self.logger.info(
                f"Scanning for entity type definitions in: {self._entity_schema_def_dir}"
            )
            if os.path.isdir(self._entity_schema_def_dir):  # Check if it's a directory
                for filename in os.listdir(self._entity_schema_def_dir):
                    if filename.endswith(".hy"):
                        filepath = os.path.join(self._entity_schema_def_dir, filename)
                        self.logger.debug(f"Parsing entity type definitions from: {filepath}")
                        try:
                            type_def_nodes = self._ast_manager.parse_file(filepath)
                            # Pass source_file for better error messages and tracking
                            self._extract_entity_types_from_nodes(
                                type_def_nodes, source_file=filename
                            )
                        except Exception as e_schema_file:
                            self.logger.error(
                                f"Error parsing entity schema file '{filepath}': {e_schema_file}",
                                exc_info=True,
                            )
            else:
                self.logger.warning(
                    f"Entity type definition directory not found or is not a directory: {self._entity_schema_def_dir}"
                )
            self.logger.info(
                f"Scanning for complex type definitions in: {self._complex_type_def_dir}"
            )
            if os.path.isdir(self._complex_type_def_dir):  # Check if it's a directory
                for filename in os.listdir(self._complex_type_def_dir):
                    if filename.endswith(".hy"):
                        filepath = os.path.join(self._complex_type_def_dir, filename)
                        self.logger.debug(f"Parsing complex type definitions from: {filepath}")
                        try:
                            complex_type_nodes = self._ast_manager.parse_file(filepath)
                            self._extract_complex_types_from_nodes(
                                complex_type_nodes, source_file=filename
                            )
                        except Exception as e_ctype_file:
                            self.logger.error(
                                f"Error parsing complex type file '{filepath}': {e_ctype_file}",
                                exc_info=True,
                            )
            else:
                self.logger.warning(
                    f"Complex type definition directory not found or is not a directory: {self._complex_type_def_dir}"
                )
            variables_component = self.get_component("variables")
            variables = {}

            if variables_component:
                for name, var_model in variables_component.items():
                    try:
                        var_typed_value: TypedValue = getattr(var_model, "value", var_model)

                        if not isinstance(var_typed_value, TypedValue):
                            self.logger.warning(
                                f"Variable '{name}' did not resolve to a TypedValue. "
                                "Skipping its inclusion in entity resolution context."
                            )
                            continue

                        value_for_context: Any
                        if var_typed_value.is_dynamic:
                            value_for_context = var_typed_value._raw_value
                            self.logger.debug(
                                f"Variable '{name}' is dynamic. Passing original expression for re-evaluation: {value_for_context}"
                            )
                        else:
                            value_for_context = var_typed_value.value
                            self.logger.debug(
                                f"Variable '{name}' is static. Passing resolved value: {value_for_context}"
                            )

                        variables[name] = value_for_context
                        if "-" in name and name.replace("-", "_") not in variables:
                            variables[name.replace("-", "_")] = value_for_context
                    except Exception as e_var:
                        self.logger.error(
                            f"Error processing variable '{name}' for entity context: {e_var}",
                            exc_info=True,
                        )

            self.logger.debug(
                f"EntityComponent.load() - 'variables' dict populated. Keys: {list(variables.keys())}"
            )

            context_for_entity_loading = LoaderContext(
                config_dir=self._entity_type_instances_base_dir, variables=variables
            )

            self.logger.debug(
                f"EntityComponent.load() - LoaderContext created. Its variables keys: {list(context_for_entity_loading.variables.keys())}"
            )

            self.logger.debug(
                f"Context variables for entity instance loading: {list(variables.keys())}"
            )

            if self.entity_types:
                self._register_entity_type_plugins()
                self._ensure_dirs()
                self._load_entities_from_all_category_files(context_for_entity_loading)
            else:
                self.logger.info("No entity types defined. Skipping instance loading.")

            self._loaded = True
            self.logger.info(
                f"EntityComponent loading complete. Loaded {len(self.entity_types)} entity types, "
                f"{len(self.complex_types)} complex types, and {len(self._items)} entity instances."
            )
        except Exception as e:
            self.logger.error(f"Fatal error during EntityComponent load: {e}", exc_info=True)
            self._loaded = False
            raise

    def _extract_entity_types_from_nodes(
        self, type_def_nodes: List[HyNode], source_file: str
    ) -> None:
        for node in type_def_nodes:
            if node.type != "def-entity":
                continue

            display_name = str(node.value)
            definition_kind = getattr(node, "definition_kind", "entity-type")
            if definition_kind != "entity-type":
                self.logger.debug(
                    f"Skipping node '{display_name}' in '{source_file}', kind is '{definition_kind}', expected 'entity-type'."
                )
                continue

            entity_type_key = display_name.lower()

            if entity_type_key in self.entity_types:
                self.logger.error(
                    f"Duplicate entity type definition for '{entity_type_key}' (from display name '{display_name}'). "
                    f"Found in '{source_file}', but already defined from '{self.entity_types[entity_type_key].get('source_file', 'unknown file')}'. "
                    f"Entity type names must be globally unique. Skipping this definition."
                )
                continue

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
                        f"Error converting schema for '{attr_name_str}' of entity type '{display_name}' from '{source_file}': {e_conv}",
                        exc_info=True,
                    )

            self.entity_types[entity_type_key] = {
                "name": display_name,
                "attributes_schema": processed_py_attr_schemas,
                "source_file": source_file,
            }
            self.logger.info(
                f"Extracted schema for entity type '{entity_type_key}' (Display: '{display_name}') from '{source_file}'."
            )

    def _extract_complex_types_from_nodes(
        self, complex_type_nodes: List[HyNode], source_file: str
    ) -> None:
        for node in complex_type_nodes:
            if node.type != "def-complex-type":
                continue

            complex_type_name = str(node.value)
            if complex_type_name in self.complex_types:
                self.logger.error(
                    f"Duplicate complex type definition for '{complex_type_name}'. "
                    f"Found in '{source_file}', but already defined from '{self.complex_types[complex_type_name].get('source_file', 'unknown file')}'. "
                    f"Complex type names must be globally unique. Skipping this definition."
                )
                continue

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
                        f"Error converting schema for attribute '{attr_name_str}' of complex type '{complex_type_name}' from '{source_file}': {e_conv}",
                        exc_info=True,
                    )

            self.complex_types[complex_type_name] = {
                "name": complex_type_name,
                "attributes_schema": processed_py_attr_schemas,
                "source_file": source_file,
            }
            self.logger.info(
                f"Extracted schema for complex type '{complex_type_name}' from '{source_file}'."
            )

    def _register_entity_type_plugins(self) -> None:
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
        self.logger.debug(
            f"_load_entities_from_all_category_files called. Context variables keys: {list(context.variables.keys())}"
        )
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
                    entity_schema_for_loader = self.entity_types.get(
                        entity_type_key.lower(), {}
                    ).get("attributes_schema", {})
                    complex_types_for_loader = self.complex_types

                    category_context = LoaderContext(
                        config_dir=context.config_dir,
                        variables=context.variables,
                        current_category=category_name,
                        current_entity_type=entity_type_key,
                        current_entity_schema=entity_schema_for_loader,
                        known_complex_type_schemas=complex_types_for_loader,
                    )
                    self.logger.debug(
                        f"category_context created. Its variables keys: {list(category_context.variables.keys())}"
                    )

                    loaded_instances = self._loader.process(instance_nodes, category_context)
                    total_instances_loaded_all_types += len(loaded_instances)
                except Exception as e_file:
                    self.logger.error(f"Error loading from '{filepath}': {e_file}", exc_info=True)
        self.logger.debug(
            f"Total instances from category files: {total_instances_loaded_all_types}"
        )

    def get_complex_type_schema(self, complex_type_name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the processed schema for a given complex type name.
        """
        complex_type_def = self.complex_types.get(complex_type_name)
        if complex_type_def:
            return complex_type_def.get("attributes_schema")
        self.logger.warning(f"Schema for complex type '{complex_type_name}' not found.")
        return None

    def save(self) -> None:
        self.logger.info("Saving entity type schemas...")
        self._ensure_dirs()
        schema_plugin = plugin_registry.get_node_plugin("def-entity")
        if not schema_plugin:
            self.logger.error("Schema plugin 'def-entity' not found. Cannot save schemas")
        else:
            schemas_by_file: Dict[str, List[Dict[str, Any]]] = {}
            for entity_type_key, schema_def in self.entity_types.items():
                source_filename = schema_def.get("source_file", "default.hy")
                if source_filename not in schemas_by_file:
                    schemas_by_file[source_filename] = []
                schemas_by_file[source_filename].append(schema_def)

            for source_filename, schemas_in_file in schemas_by_file.items():
                output_filepath = os.path.join(self._entity_schema_def_dir, source_filename)
                type_def_hy_lines = []

                sorted_schemas = sorted(schemas_in_file, key=lambda s: s.get("name", ""))

                for schema_def in sorted_schemas:
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
                    node_for_formatting = HyNode(type="def-entity", value=display_name)
                    setattr(node_for_formatting, "definition_kind", "entity-type")
                    setattr(
                        node_for_formatting, "attribute_schemas_raw_hy", attr_schemas_for_hy_node
                    )
                    type_def_hy_lines.extend(schema_plugin.format(node_for_formatting))
                    type_def_hy_lines.append("")
                try:
                    with open(output_filepath, "w", encoding="utf-8") as f:
                        f.write("\n".join(type_def_hy_lines))
                    self.logger.info(
                        f"Saved {len(self.entity_types)} entity type defs to {output_filepath}"
                    )
                except Exception as e_save_schema:
                    self.logger.error(
                        f"Error saving entity type defs: {e_save_schema}", exc_info=True
                    )

        instances_by_type_and_category: Dict[str, Dict[str, List[Entity]]] = {}
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
                    fresh_attributes_typed = {}
                    for attr_name, tv in entity_instance.get_all_attributes_typed().items():
                        # Re-create the TypedValue from its own properties.
                        fresh_attributes_typed[attr_name] = TypedValue(
                            value=tv.value,
                            field_type=tv.field_type,
                            is_dynamic=tv.is_dynamic,
                            original=tv.original,
                            item_type=tv.item_type,
                            enum_choices=tv.enum_choices,
                            item_schema_type=tv.item_schema_type,
                            referenced_entity_type=tv.referenced_entity_type,
                            referenced_entity_category=tv.referenced_entity_category,
                        )

                    setattr(
                        node_for_formatting,
                        "attributes_typed",
                        fresh_attributes_typed,  # Use the fresh dictionary
                    )
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
            if os.path.basename(empty_filepath).lower() != "default.hy":
                try:
                    os.remove(empty_filepath)
                    self.logger.info(f"Removed empty category file: {empty_filepath}")
                except OSError as e_remove:
                    self.logger.error(f"Error removing {empty_filepath}: {e_remove}")
        self.logger.info("Entities saving complete.")

    def _get_entity_schema(self, entity_type_str: str) -> Optional[Dict[str, Any]]:
        type_def = self.entity_types.get(entity_type_str.lower())
        return type_def.get("attributes_schema") if type_def else None

    def get_entity(self, entity_type: str, category: str, name: str) -> Optional[Entity]:
        """
        Get a specific entity by its unique type, category, and name.
        """
        if not category:  # Ensure category is provided
            self.logger.warning(
                "get_entity called without a category. Category is required for unique lookup."
            )
            # Or raise ValueError("Category is required for get_entity")
            return None

        # Use the new category-aware method from EntityManager
        return self._entity_manager.get_by_name_type_category(
            name=name,
            entity_type=entity_type.lower(),
            category=category.lower(),  # Ensure category is normalized
        )

    def get_by_type(self, entity_type: str, category: Optional[str] = None) -> List[Entity]:
        """
        Get all entities of a specific type, optionally filtered by category.
        """
        # The manager's get_by_type now handles category filtering.
        return self._entity_manager.get_by_type(entity_type.lower(), category)

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

    def create_entity(
        self,
        name: str,
        entity_type: str,
        attributes_raw: Optional[Dict[str, Any]] = None,
        category: str = "default",  # Added category parameter
    ) -> Entity:
        self.logger.debug(
            f"Component.create_entity: name='{name}', type='{entity_type}', category='{category}', raw_attrs='{attributes_raw}'"
        )
        entity_type_key = entity_type.lower().strip()
        category_key = sanitize_filename(
            category.strip().lower() if category and category.strip() else "default"
        )
        name_key = name.strip()

        if not name_key:
            raise ValueError("Entity name cannot be empty.")
        if not entity_type_key:
            raise ValueError("Entity type cannot be empty.")

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

            item_schema_type_from_schema = attr_schema_details.get("item_schema_type")
            ref_entity_type_from_schema = attr_schema_details.get("referenced_entity_type")
            ref_entity_cat_from_schema = attr_schema_details.get("referenced_entity_category")

            is_dynamic_attr_flag = False
            original_expr_str = None
            value_for_tv_constructor = raw_value_from_api

            if (
                isinstance(raw_value_from_api, str)
                and raw_value_from_api.strip().startswith("(")
                and raw_value_from_api.strip().endswith(")")
            ):
                is_dynamic_attr_flag = True
                original_expr_str = raw_value_from_api
                if field_type_enum not in [
                    FieldType.CODE,
                    FieldType.DATETIME,
                    FieldType.ENTITY_REFERENCE,
                ]:  # Types that store expressions directly
                    try:
                        resolved_val_raw, _ = self._loader._dynamic_service.evaluate(
                            expression=original_expr_str,
                            context=variables_for_eval_context,
                            component_type=f"entity.{entity_type_key}",
                            component_label=f"{category_key}:{name_key}",
                            attribute=attr_name,
                        )
                        value_for_tv_constructor = hy_to_python(resolved_val_raw)
                    except Exception as e_resolve:  # pragma: no cover
                        self.logger.error(
                            f"Resolve fail in create for '{attr_name}': {e_resolve}. Storing original or None."
                        )
                        value_for_tv_constructor = (
                            original_expr_str if field_type_enum == FieldType.CODE else None
                        )

            final_typed_attributes[attr_name] = TypedValue(
                value=value_for_tv_constructor,
                field_type=field_type_enum,
                is_dynamic=is_dynamic_attr_flag,
                original=original_expr_str,
                enum_choices=enum_choices,
                item_type=item_type_enum,
                item_schema_type=item_schema_type_from_schema,
                referenced_entity_type=ref_entity_type_from_schema,
                referenced_entity_category=ref_entity_cat_from_schema,
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

        entity_instance = self._entity_manager.create(
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
        category: str,
        name: str,
        attr_name: str,
        new_raw_value_from_api: Any,
        is_new_value_dynamic: bool = False,
        new_original_expression: Optional[str] = None,
    ):
        entity = self.get_entity(entity_type, category, name)
        if not entity:
            raise ValueError(f"Entity {entity_type}:{category}:{name} not found for update.")
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
                    component_type=f"entity.{entity_type.lower()}",
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
            f"Updated attribute '{attr_name}' for entity '{entity_type}:{category}:{name}'. New TV: {repr(updated_typed_value)}"
        )

    def remove_entity(self, entity_type: str, category: str, name: str) -> None:
        """Remove an entity by its unique type, category, and name."""
        entity_type_key = entity_type.lower().strip()
        category_key = category.strip().lower() if category and category.strip() else "default"
        name_key = name.strip()

        if not self._entity_manager.remove_entity(name_key, entity_type_key, category_key):
            self.logger.warning(
                f"Entity not found in manager for removal: type='{entity_type_key}', category='{category_key}', name='{name_key}'"
            )
        else:
            self.save()
            self.logger.info(f"Removed entity: {entity_type_key}:{category_key}:{name_key}")

    def rename_entity(
        self,
        entity_type: str,
        old_category: str,
        old_name: str,
        new_name: str,
        new_category: Optional[str] = None,
    ) -> None:
        entity_type_key = entity_type.lower().strip()
        old_category_key = (
            old_category.strip().lower() if old_category and old_category.strip() else "default"
        )
        old_name_key = old_name.strip()
        new_name_key = new_name.strip()
        new_category_key = (
            new_category.strip().lower()
            if new_category and new_category.strip()
            else old_category_key
        )
        if not new_name_key:
            raise ValueError("New entity name cannot be empty.")
        entity_to_rename = self._entity_manager.get_by_name_type_category(
            old_name_key, entity_type_key, old_category_key
        )
        if not entity_to_rename:
            raise ValueError(
                f"Entity to rename not found: {entity_type_key}:{old_category_key}:{old_name_key}"
            )
        if old_name_key != new_name_key or old_category_key != new_category_key:
            if self._entity_manager.get_by_name_type_category(
                new_name_key, entity_type_key, new_category_key
            ):
                raise ValueError(
                    f"New entity identifier already exists: {entity_type_key}:{new_category_key}:{new_name_key}"
                )
        self._entity_manager.remove_entity(old_name_key, entity_type_key, old_category_key)
        entity_to_rename.name = new_name_key
        entity_to_rename.category = new_category_key
        self._entity_manager.create(
            name=entity_to_rename.name,
            entity_type=entity_to_rename.entity_type,
            category=entity_to_rename.category,
            attributes=entity_to_rename.attributes,
        )

        self.save()  # Persist changes
        self.logger.info(
            f"Renamed entity from '{entity_type_key}:{old_category_key}:{old_name_key}' "
            f"to '{entity_type_key}:{new_category_key}:{new_name_key}'."
        )

    def get_categories(self, entity_type_str: str) -> List[str]:
        entity_type_key = entity_type_str.lower()
        type_specific_dir = os.path.join(
            self._entity_type_instances_base_dir, f"{entity_type_key}s"
        )
        categories = []
        if os.path.isdir(type_specific_dir):
            for filename in os.listdir(type_specific_dir):
                if filename.endswith(".hy"):
                    sanitized_name = sanitize_filename(os.path.splitext(filename)[0])
                    if sanitized_name:
                        categories.append(sanitized_name)
        unique_categories = sorted(list(set(c for c in categories if c)))
        return unique_categories

    def create_category(self, entity_type_str: str, category_name: str) -> bool:
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
        self, entity_type: str, old_category: str, entity_name: str, new_category_name: str
    ) -> bool:
        entity = self.get_entity(entity_type, old_category, entity_name)  # Correct call
        if not entity:
            self.logger.error(
                f"Entity '{entity_type}:{old_category}:{entity_name}' not found to move."
            )
            return False
        new_cat_key = sanitize_filename(
            new_category_name.lower()
            if new_category_name and new_category_name.strip()
            else "default"
        )

        self.rename_entity(
            entity_type=entity_type,
            old_category=old_category,
            old_name=entity_name,
            new_name=entity_name,  # name doesn't change
            new_category=new_cat_key,  # only category changes
        )
        return True

    def get_tasks(self, category: Optional[str] = None) -> List[Entity]:
        return self.get_by_type("task", category)

    def start_occurrence(
        self, entity_type: str, category: str, name: str, list_attribute_name: str = "occurrences"
    ) -> Entity:
        """
        Starts a new occurrence for an entity by setting its 'active_occurrence_start_time'
        and handles context switching if defined.
        """
        self.logger.debug(f"Attempting to start occurrence for {entity_type}:{category}:{name}")
        entity = self.get_entity(entity_type, category, name)
        if not entity:
            raise ValueError(f"Entity not found: {entity_type}:{category}:{name}")

        active_start_time_attr = "active_occurrence_start_time"
        if not entity.has_attribute(active_start_time_attr):
            raise TypeError(
                f"Entity '{name}' is not configured to track active occurrences (missing '{active_start_time_attr}' attribute)."
            )

        if entity.get_attribute_value(active_start_time_attr) is not None:
            raise ValueError("An occurrence is already in progress for this entity.")
        now_utc = datetime.now(timezone.utc)
        start_time_tv = TypedValue(value=now_utc, field_type=FieldType.DATETIME)

        entity.set_attribute_typed(active_start_time_attr, start_time_tv)
        self.logger.info(
            f"Set '{active_start_time_attr}' for '{name}' to {start_time_tv.value} in memory."
        )

        context_tv = entity.get_attribute_typed("context")
        if context_tv and context_tv.value:
            context_to_switch = str(context_tv.value)
            self.logger.info(
                f"Entity '{name}' has associated context: '{context_to_switch}'. Triggering switch."
            )

            try:
                daily_log_component = self.get_component("daily_logs")
                if daily_log_component is not None:
                    if not daily_log_component.is_loaded():
                        daily_log_component.load()
                    daily_log_component.switch_context(context_to_switch)
                    self.logger.info(
                        f"Successfully switched daily log context to '{context_to_switch}'."
                    )
                else:
                    self.logger.warning(
                        "DailyLogComponent not found. Cannot perform automatic context switch."
                    )
            except Exception as e:
                self.logger.error(
                    f"Failed to switch context for entity '{name}': {e}", exc_info=True
                )

        self._run_hook_code(entity, "on-start-hook", "start")
        self.save()  # This single save persists both the entity change and the daily_log change.
        return entity

    def end_occurrence(
        self,
        entity_type: str,
        category: str,
        name: str,
        notes: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        list_attribute_name: str = "occurrences",
    ) -> Entity:
        """
        Ends an in-progress occurrence, logs it to the occurrences list,
        and clears the active start time.
        """
        self.logger.debug(f"Attempting to end occurrence for {entity_type}:{category}:{name}")
        entity = self.get_entity(entity_type, category, name)
        if not entity:
            raise ValueError(f"Entity not found: {entity_type}:{category}:{name}")

        # Verify the entity has the required attributes
        active_start_time_attr = "active_occurrence_start_time"
        if not entity.has_attribute(active_start_time_attr) or not entity.has_attribute(
            list_attribute_name
        ):
            raise TypeError(f"Entity '{name}' is not configured to track occurrences.")

        start_time = entity.get_attribute_value(active_start_time_attr)
        if start_time is None:
            raise ValueError("No active occurrence was found to end for this entity.")

        from utms.utils import get_ntp_date  # Or wherever it is defined

        end_time = get_ntp_date()

        # Construct the new occurrence object
        new_occurrence_data = {
            "start_time": start_time,
            "end_time": end_time,
            "notes": notes or "",
            "metadata": metadata or {},
        }

        old_occurrences_tv = entity.get_attribute_typed(list_attribute_name)

        # Make a copy of the old list, or start a new one
        new_occurrences_list = (
            old_occurrences_tv.value.copy()
            if old_occurrences_tv and isinstance(old_occurrences_tv.value, list)
            else []
        )

        # Append the new data to our new list
        new_occurrences_list.append(new_occurrence_data)

        occurrences_tv = entity.get_attribute_typed(list_attribute_name)

        if not occurrences_tv:
            # If for some reason it doesn't exist, create it.
            occurrences_tv = TypedValue(
                value=[], field_type=FieldType.LIST, item_schema_type="OCCURRENCE"
            )
            entity.set_attribute_typed(list_attribute_name, occurrences_tv)

        # Get the current list. Ensure it's actually a list.
        current_list = occurrences_tv.value if isinstance(occurrences_tv.value, list) else []

        # Create the new, updated list
        new_list = current_list + [new_occurrence_data]

        # Set the 'value' property on the existing TypedValue.
        # This will trigger the setter, which re-runs _convert_value.
        occurrences_tv.value = new_list

        # Clear the active start time by setting it back to None
        cleared_start_time_tv = TypedValue(
            value=None, field_type=FieldType.DATETIME, original="None"
        )
        entity.set_attribute_typed(active_start_time_attr, cleared_start_time_tv)

        entity_in_method = entity  # The object we just modified
        entity_in_manager = self._entity_manager.get(f"{entity_type}:{category}:{name}")
        self.logger.info(f"Ended and logged occurrence for '{name}' in memory.")

        self._run_hook_code(entity, "on-end-hook", "end")
        self.save()
        return entity

    def _run_hook_code(self, entity: Entity, hook_attribute_name: str, event_name: str):
        """
        Finds and executes the Hy code defined in a hook attribute on an entity.

        Args:
            entity: The entity instance.
            hook_attribute_name: The name of the attribute holding the hook code (e.g., "on-start-hook").
            event_name: A string for logging (e.g., "start").
        """
        self.logger.debug(
            f"Checking for '{hook_attribute_name}' on '{entity.name}' for '{event_name}' event."
        )

        hook_tv = entity.get_attribute_typed(hook_attribute_name)

        if not hook_tv or not hook_tv.original:
            self.logger.debug(f"No hook defined for this event.")
            return

        if hook_tv.field_type != FieldType.CODE:
            self.logger.warning(
                f"Attribute '{hook_attribute_name}' on '{entity.name}' is not of type 'code'. Cannot execute. "
                f"Found type: {hook_tv.field_type}"
            )
            return

        code_to_run = hook_tv.original
        self.logger.info(f"Executing '{event_name}' hook for '{entity.name}': {code_to_run}")

        try:
            hook_context = {
                "sh": sh,
            }
            self._loader._dynamic_service.evaluate(
                expression=code_to_run,
                context=hook_context,
                component_type="entity_hook",
                component_label=f"{entity.entity_type}:{entity.category}:{entity.name}",
                attribute=hook_attribute_name,
            )
            self.logger.info(f"Successfully executed '{event_name}' hook for '{entity.name}'.")

        except Exception as e:
            # IMPORTANT: We log the error but do not re-raise it.
            # The failure of a hook should not prevent the core action (starting/ending the occurrence).
            self.logger.error(
                f"Error executing '{hook_attribute_name}' for entity '{entity.name}': {e}",
                exc_info=True,
            )
