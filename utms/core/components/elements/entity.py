import os
import shutil
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Union
import pickle
import hashlib
from decimal import Decimal

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
from utms.core.hy.converter import converter
from utms.utils import list_to_dict, sanitize_filename
from utms.utms_types import HyNode
from utms.utms_types.field.types import FieldType, TypedValue, infer_type
from utms.utils import get_ntp_date
from dataclasses import dataclass
from utms.core.hy.converter import py_list_to_hy_expression

@dataclass
class CachedEntityData:
    """A simple, pickle-safe container for entity data."""
    name: str
    entity_type: str
    category: str
    attributes: Dict[str, Dict[str, Any]]


class EntityComponent(SystemComponent):
    """Component managing UTMS entities with TypedValue attributes and categories."""

    def __init__(self, config_dir: str, component_manager=None):
        super().__init__(config_dir, component_manager)
        self._ast_manager = HyAST()
        self._entity_manager = EntityManager()
        self._loader = EntityLoader(self._entity_manager, component=self)

        config_component = self.get_component("config")
        if not config_component.is_loaded():
            config_component.load()

        active_user = config_component.get_config("active-user")
        user_specific_dir = os.path.join(self._config_dir, "users", active_user.get_value())
        self.logger.info(f"EntityComponent is now operating in user-specific directory: {user_specific_dir}")

        self._entity_schema_def_dir = os.path.join(user_specific_dir, "entities")
        self._complex_type_def_dir = os.path.join(user_specific_dir, "types")

        self._entity_type_instances_base_dir = user_specific_dir

        self.entity_types: Dict[str, Dict[str, Any]] = {}
        self.complex_types: Dict[str, Dict[str, Any]] = {}
        self._file_mod_times: Dict[str, float] = {}
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

    def _get_cache_path_for_file(self, source_filepath: str) -> str:
        """Generates a unique, safe cache file path for a given source file."""
        abs_path = os.path.abspath(source_filepath)
        path_hash = hashlib.md5(abs_path.encode('utf-8')).hexdigest()
        cache_dir = os.path.join(os.path.expanduser("~"), ".cache", "utms", "entities")
        os.makedirs(cache_dir, exist_ok=True)

        return os.path.join(cache_dir, f"{path_hash}.pkl")

    def load(self) -> None:
        if self._loaded:
            self.logger.debug("EntityComponent already loaded.")
            return
        self.logger.info("Loading Entities...")
        self._entity_manager.clear()
        self.entity_types = {}
        self.complex_types = {}

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
            if os.path.isdir(self._complex_type_def_dir):  
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
            variables = {name: var.value for name, var in variables_component.items()}
            self.logger.debug(f"Entity loader context populated with variables: {list(variables.keys())}")

            if variables_component:
                for name, var_model in variables_component.items():
                    try:
                        typed_value_obj = getattr(var_model, "value", None)

                        if not isinstance(typed_value_obj, TypedValue):
                            self.logger.warning(
                                f"Variable '{name}' did not resolve to a TypedValue. "
                                "Skipping its inclusion in entity resolution context."
                            )
                            continue
                        value_for_context = typed_value_obj.value 
                        
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

            self.logger.info("Rebuilding resource claim map from persisted active entities...")
            active_entities_on_load = self._entity_manager.get_all_active_entities()
            for entity in active_entities_on_load:
                if entity.get_exclusive_resource_claims():
                    self._entity_manager.register_claims(entity)
                    self.logger.debug(f"Re-registered claims for active entity: {entity.get_identifier()}")
            self.logger.info(f"Resource claim map rebuilt. {len(active_entities_on_load)} active entities found.")

            self._loaded = True
            self.logger.info(
                f"EntityComponent loading complete. Loaded {len(self.entity_types)} entity types, "
                f"{len(self.complex_types)} complex types, and {len(self._items)} entity instances."
            )
        except Exception as e:
            self.logger.error(f"Fatal error during EntityComponent load: {e}", exc_info=True)
            self._loaded = False
            raise

    def get_sanitized_entity_schema(self, entity_type_str: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the schema for an entity type and returns a fully sanitized,
        Python-native dictionary version of it, safe for use in core logic.
        """
        raw_schema = self._get_entity_schema(entity_type_str)
        if not raw_schema:
            return None

        sanitized_schema: Dict[str, Dict[str, Any]] = {}
        for attr_name, attr_schema_hy_dict in raw_schema.items():
            if isinstance(attr_schema_hy_dict, hy.models.Dict):
                try:
                    py_list = converter.model_to_py(attr_schema_hy_dict, raw=True)
                    sanitized_schema[attr_name] = list_to_dict(py_list)
                except Exception as e_conv:
                    self.logger.error(f"Failed to sanitize schema for '{entity_type_str}.{attr_name}': {e_conv}")
                    sanitized_schema[attr_name] = {} 
            elif isinstance(attr_schema_hy_dict, dict):
                sanitized_schema[attr_name] = attr_schema_hy_dict
            else:
                 self.logger.warning(f"Unexpected schema format for '{entity_type_str}.{attr_name}': {type(attr_schema_hy_dict)}")
                 sanitized_schema[attr_name] = {}

        return sanitized_schema

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

            canonical_hy_attr_schemas: Dict[str, hy.models.HyObject] = {}
            for attr_name_from_file, attr_schema_hy_obj in raw_hy_attr_schemas.items():
                canonical_name = str(attr_name_from_file).replace('_', '-')
                if canonical_name in canonical_hy_attr_schemas:
                    self.logger.warning(f"Duplicate attribute definition after normalization for '{attr_name_from_file}' ...")
                canonical_hy_attr_schemas[canonical_name] = attr_schema_hy_obj

            processed_py_attr_schemas: Dict[str, Dict[str, Any]] = {}
            for attr_name_str, attr_schema_hy_dict in canonical_hy_attr_schemas.items():
                if not isinstance(attr_schema_hy_dict, hy.models.Dict):
                    self.logger.warning(f"Schema for attribute '{attr_name_str}' ... is not a valid HyDict. Skipping.")
                    continue
                try:
                    py_list = converter.model_to_py(attr_schema_hy_dict, raw=True)
                    py_dict = list_to_dict(py_list)
                    processed_py_attr_schemas[attr_name_str] = py_dict
                except Exception as e_conv:
                    self.logger.error(f"Error converting schema for attribute '{attr_name_str}' ...: {e_conv}", exc_info=True)

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
                    py_schema_list_of_pairs = converter.model_to_py(attr_schema_hy_dict, raw=True)
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
            plugin_node_type = f"def-{entity_type_key}"
            if plugin_registry.has_plugin(plugin_node_type):
                self.logger.debug(f"Plugin for '{plugin_node_type}' already exists. Skipping registration.")
                continue
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
                filepath = os.path.join(type_specific_instance_dir, filename)
                try:
                    self._file_mod_times[filepath] = os.path.getmtime(filepath)
                except FileNotFoundError:
                    continue
                cache_filepath = self._get_cache_path_for_file(filepath)

                is_cache_valid = False
                if os.path.exists(cache_filepath):
                    try:
                        if os.path.getmtime(filepath) <= os.path.getmtime(cache_filepath):
                            is_cache_valid = True
                    except FileNotFoundError:
                        is_cache_valid = False

                if is_cache_valid:
                    self.logger.debug(f"CACHE HIT for '{filepath}'. Loading from cache.")
                    try:
                        with open(cache_filepath, 'rb') as f:
                            cached_data_list: List[CachedEntityData] = pickle.load(f)

                        for cached_data in cached_data_list:
                            deserialized_attributes = {
                                attr_name: TypedValue.deserialize(attr_data)
                                for attr_name, attr_data in cached_data.attributes.items()
                            }
                            self._entity_manager.create(
                                name=cached_data.name,
                                entity_type=cached_data.entity_type,
                                category=cached_data.category,
                                attributes=deserialized_attributes,
                            )

                        total_instances_loaded_all_types += len(cached_data_list)
                        continue

                    except Exception as e_cache:
                        self.logger.warning(f"Failed to load from cache file '{cache_filepath}': {e_cache}. Falling back to full load.")
                self.logger.debug(f"CACHE MISS for '{filepath}'. Performing full load.")
                category_name = sanitize_filename(os.path.splitext(filename)[0])
                try:
                    instance_nodes = self._ast_manager.parse_file(filepath)
                    if not instance_nodes:
                        if os.path.exists(cache_filepath):
                            os.remove(cache_filepath)
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
                        source_file=filepath,
                    )
                    loaded_instances_dict = self._loader.process(instance_nodes, category_context)
                    loaded_entities_list = list(loaded_instances_dict.values())
                    try:
                        entities_to_cache = []
                        for entity in loaded_entities_list:
                            serialized_attributes = {
                                attr_name: tv.serialize()
                                for attr_name, tv in entity.get_all_attributes_typed().items()
                            }
                            entities_to_cache.append(
                                CachedEntityData(
                                    name=entity.name,
                                    entity_type=entity.entity_type,
                                    category=entity.category,
                                    attributes=serialized_attributes
                                )
                            )
                        with open(cache_filepath, 'wb') as f:
                            pickle.dump(entities_to_cache, f)
                        self.logger.debug(f"Cache created for '{filepath}' at '{cache_filepath}'.")
                    except Exception as e_cache_write:
                        self.logger.error(f"Failed to write cache file '{cache_filepath}': {e_cache_write}", exc_info=True)


                    total_instances_loaded_all_types += len(loaded_instances_dict)


                except Exception as e_file:
                    self.logger.error(f"Error loading from '{filepath}': {e_file}", exc_info=True)
                    if os.path.exists(cache_filepath):
                        os.remove(cache_filepath)

        self.logger.debug(
            f"Total instances from category files: {total_instances_loaded_all_types}"
        )


    def sync_from_disk(self) -> None:
        """Efficiently syncs in-memory entities with changes on disk."""
        self.logger.debug("Checking for entity file changes on disk...")
        
        variables_component = self.get_component("variables")
        variables = {}
        if variables_component:
            for name, var in variables_component.items():
                if hasattr(var, 'value') and isinstance(var.value, TypedValue):
                    raw_value = var.value.value
                    variables[name] = raw_value
                    if '-' in name:
                        variables[name.replace('-', '_')] = raw_value
        context = LoaderContext(config_dir=self._entity_type_instances_base_dir, variables=variables)

        all_current_files = set()
        for entity_type_key in self.entity_types.keys():
            type_dir = os.path.join(self._entity_type_instances_base_dir, f"{entity_type_key}s")
            if not os.path.isdir(type_dir): continue

            for filename in os.listdir(type_dir):
                if not filename.endswith(".hy") or filename.startswith('.'): continue
                
                filepath = os.path.join(type_dir, filename)
                all_current_files.add(filepath)

                try:
                    current_mtime = os.path.getmtime(filepath)
                except FileNotFoundError: continue

                last_mtime = self._file_mod_times.get(filepath)

                if last_mtime is None or current_mtime > last_mtime:
                    self.logger.info(f"Detected change in '{filepath}'. Reloading it.")
                    
                    self._entity_manager.remove_by_source_file(filepath)
                    
                    category_name = sanitize_filename(os.path.splitext(filename)[0])
                    category_context = LoaderContext(
                        config_dir=context.config_dir,
                        variables=context.variables,
                        current_category=category_name,
                        current_entity_type=entity_type_key,
                        current_entity_schema=self.entity_types.get(entity_type_key.lower(), {}).get("attributes_schema", {}),
                        known_complex_type_schemas=self.complex_types,
                        source_file=filepath,
                    )

                    try:
                        instance_nodes = self._ast_manager.parse_file(filepath)
                        self._loader.process(instance_nodes, category_context)
                    except Exception as e:
                        self.logger.error(f"Failed to reload file '{filepath}': {e}", exc_info=True)

                    self._file_mod_times[filepath] = current_mtime

        deleted_files = set(self._file_mod_times.keys()) - all_current_files
        for filepath in deleted_files:
            self.logger.info(f"Detected deletion of '{filepath}'. Removing its entities.")
            self._entity_manager.remove_by_source_file(filepath)
            del self._file_mod_times[filepath]


    def get_complex_type_schema(self, complex_type_name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the processed schema for a given complex type name.
        """
        complex_type_def = self.complex_types.get(complex_type_name)
        if complex_type_def:
            return complex_type_def.get("attributes_schema")
        self.logger.warning(f"Schema for complex type '{complex_type_name}' not found.")
        return None

    def save_schemas(self):
        """Saves only the entity type schema definitions (def-entity) to disk."""
        self.logger.info("Saving entity type schemas...")
        self._ensure_dirs()
        schema_plugin = plugin_registry.get_node_plugin("def-entity")
        if not schema_plugin:
            self.logger.error("Schema plugin 'def-entity' not found. Cannot save schemas")
            return # Return early

        schemas_by_file: Dict[str, List[Dict[str, Any]]] = {}
        for entity_type_key, schema_def in self.entity_types.items():
            source_filename = schema_def.get("source_file", "default.hy")
            schemas_by_file.setdefault(source_filename, []).append(schema_def)

        for source_filename, schemas_in_file in schemas_by_file.items():
            output_filepath = os.path.join(self._entity_schema_def_dir, source_filename)
            type_def_hy_lines = []

            sorted_schemas = sorted(schemas_in_file, key=lambda s: s.get("name", ""))

            for schema_def in sorted_schemas:
                display_name = schema_def["name"]
                python_attr_schemas = schema_def["attributes_schema"]

                node_for_formatting = HyNode(type="def-entity", value=display_name)
                setattr(node_for_formatting, "definition_kind", "entity-type")
                setattr(node_for_formatting, "attribute_schemas_raw_hy", python_attr_schemas)
                type_def_hy_lines.extend(schema_plugin.format(node_for_formatting))
                type_def_hy_lines.append("")
            try:
                with open(output_filepath, "w", encoding="utf-8") as f:
                    f.write("\n".join(type_def_hy_lines))
                self.logger.info(
                    f"Saved {len(schemas_in_file)} entity type defs to {output_filepath}"
                )
            except Exception as e_save_schema:
                self.logger.error(
                    f"Error saving entity type defs to '{output_filepath}': {e_save_schema}", exc_info=True
                )

    def _save_entities_in_category(self, entity_type: str, category: str):
        entity_type_key = entity_type.lower()
        category_key = category.lower()

        entities_to_save = [e for e in self._items.values() if e.entity_type == entity_type_key and e.category == category_key]
        
        type_specific_dir = os.path.join(self._entity_type_instances_base_dir, f"{entity_type_key}s")
        if not os.path.exists(type_specific_dir): os.makedirs(type_specific_dir)
        category_filename = f"{sanitize_filename(category_key)}.hy"
        instance_file_path = os.path.join(type_specific_dir, category_filename)

        if not entities_to_save:
            if os.path.exists(instance_file_path):
                self.logger.info(f"Last entity from '{instance_file_path}' removed. Deleting empty category file.")
                try: os.remove(instance_file_path)
                except OSError as e_remove: self.logger.error(f"Error removing empty category file {instance_file_path}: {e_remove}")
            return

        instance_plugin = plugin_registry.get_node_plugin(f"def-{entity_type_key}")
        if not instance_plugin:
            self.logger.warning(f"No plugin for 'def-{entity_type_key}'. Cannot save entities for category '{category_key}'.")
            return

        instance_hy_lines = []
        for entity_instance in sorted(entities_to_save, key=lambda inst: inst.name):
            node_for_formatting = HyNode(type=f"def-{entity_type_key}", value=entity_instance.name)

            attributes_for_formatting = entity_instance.get_all_attributes_typed()

            for attr_name, attr_tv in attributes_for_formatting.items():
                if attr_tv.field_type == FieldType.LIST and attr_tv.item_schema_type:
                    if isinstance(attr_tv.value, list):
                        
                        final_hy_objects = []
                        for item in attr_tv.value:
                            if isinstance(item, hy.models.Object):
                                final_hy_objects.append(item)
                                continue

                            py_dict = {}
                            if isinstance(item, list):      
                                py_dict = list_to_dict(item)
                            elif isinstance(item, dict):    
                                py_dict = item
                            else:
                                continue 

                            final_hy_objects.append(converter.py_to_model(py_dict))
                        attr_tv.value = hy.models.List(final_hy_objects)
                        final_hy_list_object = hy.models.List(final_hy_objects)
                        
                        adapted_tv = TypedValue(
                            value=final_hy_list_object,
                            field_type=attr_tv.field_type,
                            item_schema_type=attr_tv.item_schema_type
                        )
                        adapted_tv._value = final_hy_list_object
                        attributes_for_formatting[attr_name] = adapted_tv
            setattr(node_for_formatting, "attributes_typed", attributes_for_formatting)
            instance_hy_lines.extend(instance_plugin.format(node_for_formatting))
            instance_hy_lines.append("")

        try:
            with open(instance_file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(instance_hy_lines))
            self.logger.info(f"Saved {len(entities_to_save)} entities of type '{entity_type_key}' (cat: '{category_key}') to {instance_file_path}")
        except Exception as e_save_inst:
            self.logger.error(f"Error saving entities to '{instance_file_path}': {e_save_inst}", exc_info=True)


    def _get_entity_schema(self, entity_type_str: str) -> Optional[Dict[str, Any]]:
        type_def = self.entity_types.get(entity_type_str.lower())
        return type_def.get("attributes_schema") if type_def else None

    def get_entity(self, entity_type: str, category: str, name: str) -> Optional[Entity]:
        """
        Get a specific entity by its unique type, category, and name.
        """
        if not category:
            self.logger.warning(
                "get_entity called without a category. Category is required for unique lookup."
            )
            return None

        return self._entity_manager.get_by_name_type_category(
            name=name,
            entity_type=entity_type.lower(),
            category=category.lower(),  
        )

    def get_by_type(self, entity_type: str, category: Optional[str] = None) -> List[Entity]:
        """
        Get all entities of a specific type, optionally filtered by category.
        """
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
        return list(self.entity_types.keys())  

    def get_all_entity_type_details(self) -> List[Dict[str, Any]]:
        if not self._loaded:
            self.load()
        details = []
        for type_key_lower, type_data_dict in self.entity_types.items():
            raw_attributes_schema = type_data_dict.get("attributes_schema", {})
            pythonic_attributes_schema = {}
            if isinstance(raw_attributes_schema, dict):
                for attr_name, hy_schema_obj in raw_attributes_schema.items():
                    list_of_pairs = converter.model_to_py(hy_schema_obj, raw=True)
                    if isinstance(list_of_pairs, list):
                        pythonic_attributes_schema[attr_name] = list_to_dict(list_of_pairs)
                    else:
                        pythonic_attributes_schema[attr_name] = list_of_pairs

            details.append(
                {
                    "name": type_key_lower,
                    "displayName": type_data_dict.get("name", type_key_lower.upper()),
                    "attributes": pythonic_attributes_schema,
                }
            )
        return details

    def create_entity(
        self,
        name: str,
        entity_type: str,
        attributes_raw: Optional[Dict[str, Any]] = None,
        category: str = "default",
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

        schema = self.get_sanitized_entity_schema(entity_type_key) or {}
        raw_attributes_to_process = attributes_raw or {}

        for attr_name, attr_schema in schema.items():
            if attr_name not in raw_attributes_to_process:
                if "default_value" in attr_schema:
                    default_value = attr_schema.get("default_value")
                    if isinstance(default_value, hy.models.Symbol) and str(default_value) == "None":
                        raw_attributes_to_process[attr_name] = None
                        self.logger.info(
                            f"Enforcing schema for '{name}': Attribute '{attr_name}' was missing, applying default value: None (Python object)"
                        )
                    else:
                        raw_attributes_to_process[attr_name] = default_value
                        self.logger.info(
                            f"Enforcing schema for '{name}': Attribute '{attr_name}' was missing, applying default value: {default_value}"
                        )
                    self.logger.info(
                        f"Schema applied for '{name}': Attribute '{attr_name}' was missing, applying default value: {default_value}"
                    )

        final_typed_attributes: Dict[str, TypedValue] = {}
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

            if isinstance(raw_value_from_api, str) and raw_value_from_api.strip().startswith("("):
                is_dynamic_attr_flag = True
                original_expr_str = raw_value_from_api
                if field_type_enum not in [FieldType.CODE]:
                    value_for_tv_constructor = None

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


        for attr_name_check, attr_schema_detail in schema.items():
            is_required = attr_schema_detail.get("required") == True or str(attr_schema_detail.get("required")).lower() == "true"
            has_default = "default_value" in attr_schema_detail

            if is_required and not has_default and attr_name_check not in final_typed_attributes:
                error_msg = f"Attribute '{attr_name_check}' is required for entity type '{entity_type_key}' but was not provided and has no default."
                self.logger.warning(error_msg)
                raise ValueError(error_msg)

        entity_instance = self._entity_manager.create(
            name=name,
            entity_type=entity_type_key,
            attributes=final_typed_attributes,
            category=category_key,
        )
        self._save_entities_in_category(entity_type_key, category_key)
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
        schema = self.get_sanitized_entity_schema(entity_type.lower()) or {}
        attr_schema_details = schema.get(attr_name, {})
        
        existing_typed_value = entity.get_attribute_typed(attr_name)
        
        declared_type_str = attr_schema_details.get("type")
        if existing_typed_value:
            field_type_for_new_tv = existing_typed_value.field_type
        elif declared_type_str:
            field_type_for_new_tv = FieldType.from_string(declared_type_str)
        else:
            field_type_for_new_tv = infer_type(new_raw_value_from_api)

        item_type_str = attr_schema_details.get("item_type")
        item_type_enum = FieldType.from_string(item_type_str) if item_type_str else None
        item_schema_type_from_schema = attr_schema_details.get("item_schema_type")
        enum_choices = attr_schema_details.get("enum_choices", [])
        
        value_to_store = new_raw_value_from_api
        final_original_expr = new_original_expression if is_new_value_dynamic else None
        
        updated_typed_value = TypedValue(
            value=value_to_store,
            field_type=field_type_for_new_tv,
            is_dynamic=is_new_value_dynamic,
            original=final_original_expr,
            enum_choices=enum_choices,
            item_type=item_type_enum,
            item_schema_type=item_schema_type_from_schema
        )
        entity.set_attribute_typed(attr_name, updated_typed_value)
        self._save_entities_in_category(entity_type, category)
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
            self._save_entities_in_category(entity_type_key, category_key)
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

        self._save_entities_in_category(entity_type_key, old_category_key)  
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
            return True
        except Exception as e:
            self.logger.error(f"Error deleting category '{category_name}': {e}", exc_info=True)
            return False

    def move_entity_to_category(
        self, entity_type: str, old_category: str, entity_name: str, new_category_name: str
    ) -> bool:
        entity = self.get_entity(entity_type, old_category, entity_name)  
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
            new_name=entity_name,  
            new_category=new_cat_key,
        )
        return True

    def get_tasks(self, category: Optional[str] = None) -> List[Entity]:
        return self.get_by_type("task", category)

    def get_all_active_entities(self) -> List[Entity]:
        """
        Ensures all entities are loaded and then returns a list of all entities
        that currently have an active occurrence (a "running timer").

        This is the safe, public-facing way to get this information.
        """

        if not self._loaded:
            self.logger.info("get_all_active_entities called, ensuring full load first.")
            self.load()

        return self._entity_manager.get_all_active_entities()

    def start_occurrence(
        self, entity_type: str, category: str, name: str, list_attribute_name: str = "occurrences" 
    ) -> Entity:
        self.logger.debug(f"Attempting to start occurrence for {entity_type}:{category}:{name}")
        entity_to_start = self.get_entity(entity_type, category, name) 

        if not entity_to_start:
            raise ValueError(f"Entity not found: {entity_type}:{category}:{name}")

        active_start_time_attr = "active_occurrence_start_time" 
        if not entity_to_start.has_attribute(active_start_time_attr):
            raise TypeError(
                f"Entity '{name}' (type: {entity_type}) is not configured to track active occurrences "
                f"(missing '{active_start_time_attr}' attribute in its schema or instance)."
            )

        if entity_to_start.get_attribute_value(active_start_time_attr) is not None:
            raise ValueError(f"An occurrence is already in progress for entity '{name}'.")

        if entity_to_start.has_attribute("checklist"):
            self.logger.info(f"Resetting checklist state for new occurrence of '{entity_to_start.get_identifier()}'.")
            checklist_tv = entity_to_start.get_attribute_typed("checklist")
            
            if checklist_tv and isinstance(checklist_tv.value, list):
                updated_checklist_items = []
                for i, item in enumerate(checklist_tv.value):
                    py_dict = {}
                    if isinstance(item, list):
                        py_dict = list_to_dict(item)
                    elif isinstance(item, (hy.models.Dict, hy.models.Expression)):
                        item_as_plist = converter.model_to_py(item, raw=True)
                        py_dict = list_to_dict(item_as_plist)
                    else:
                        continue 
                    py_dict['completed'] = False
                    rebuilt_model = converter.py_to_model(py_dict)
                    updated_checklist_items.append(converter.py_to_model(py_dict))

                checklist_tv.value = updated_checklist_items

        newly_claimed_resources = entity_to_start.get_exclusive_resource_claims()
        entity_to_start_id = entity_to_start.get_identifier()

        if newly_claimed_resources:
            self.logger.info(f"Entity '{entity_to_start_id}' attempting to claim resources: {newly_claimed_resources}")
            active_entities = self._entity_manager.get_all_active_entities() 
            
            for resource_to_claim in newly_claimed_resources:
                current_holder_id = self._entity_manager.get_claiming_entity_id(resource_to_claim)
                if current_holder_id and current_holder_id != entity_to_start_id:
                    self.logger.info(
                        f"Resource '{resource_to_claim}' needed by '{entity_to_start_id}' is currently held by '{current_holder_id}'. "
                        f"Stopping '{current_holder_id}'."
                    )
                    try:
                        holder_type, holder_cat, holder_name = current_holder_id.split(":", 2)
                        self.end_occurrence(
                            entity_type=holder_type,
                            category=holder_cat,
                            name=holder_name,
                            notes=f"Auto-stopped: resource '{resource_to_claim}' needed by '{entity_to_start_id}'.",
                            _is_system_triggered=True,
                        )
                    except ValueError: 
                        self.logger.error(f"Could not parse entity identifier '{current_holder_id}' to stop it.")
                    except Exception as e:
                        self.logger.error(f"Error auto-stopping conflicting entity '{current_holder_id}': {e}", exc_info=True)
        now_utc = datetime.now(timezone.utc)
        start_time_tv = TypedValue(value=now_utc, field_type=FieldType.DATETIME)
        entity_to_start.set_attribute_typed(active_start_time_attr, start_time_tv)
        
        if newly_claimed_resources: 
            self._entity_manager.register_claims(entity_to_start)
        self.logger.info(
            f"Set '{active_start_time_attr}' for '{entity_to_start_id}' to {start_time_tv.value}."
        )

        context_tv = entity_to_start.get_attribute_typed("context")
        if context_tv and context_tv.value:
            context_to_switch = str(context_tv.value)
            self.logger.info(
                f"Entity '{entity_to_start_id}' has associated context: '{context_to_switch}'. Triggering switch."
            )
            try:
                daily_log_component = self.get_component("daily_logs")
                if daily_log_component is not None:
                    if not daily_log_component.is_loaded(): # Check if loaded
                        daily_log_component.load()
                    daily_log_component.switch_context(context_to_switch)
                    self.logger.info(
                        f"Successfully switched daily log context to '{context_to_switch}'."
                    )
                else:
                    self.logger.warning("DailyLogComponent not found. Cannot perform automatic context switch.")
            except Exception as e:
                self.logger.error(
                    f"Failed to switch context for entity '{entity_to_start_id}': {e}", exc_info=True
                )

        self._run_hook_code(entity_to_start, "on_start_hook", "start")
        self._save_entities_in_category(entity_to_start.entity_type, entity_to_start.category)
        return entity_to_start

    def end_occurrence(
        self,
        entity_type: str,
        category: str,
        name: str,
        notes: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        list_attribute_name: str = "occurrences",
        _is_system_triggered: bool = False 
    ) -> Entity:
        self.logger.debug(f"Attempting to end occurrence for {entity_type}:{category}:{name}{' (system-triggered)' if _is_system_triggered else ''}")
        entity_to_stop = self.get_entity(entity_type, category, name)
        
        if not entity_to_stop:
            raise ValueError(f"Entity not found to end occurrence: {entity_type}:{category}:{name}")

        active_start_time_attr = "active_occurrence_start_time"
        if not entity_to_stop.has_attribute(active_start_time_attr) or not entity_to_stop.has_attribute(list_attribute_name):
            raise TypeError(f"Entity '{name}' (type: {entity_type}) is not configured to track occurrences correctly.")

        start_time = entity_to_stop.get_attribute_value(active_start_time_attr)
        if start_time is None:
            if _is_system_triggered:
                 self.logger.debug(f"Entity '{entity_to_stop.get_identifier()}' was already stopped (system trigger).")
                 self._entity_manager.release_claims(entity_to_stop)
                 self._save_entities_in_category(entity_to_stop.entity_type, entity_to_stop.category)
                 return entity_to_stop
            else:
                raise ValueError(f"No active occurrence was found to end for entity '{name}'.")

        from utms.utils import get_ntp_date 
        end_time = get_ntp_date()
        new_occurrence_data = { "start_time": start_time, "end_time": end_time, "notes": notes or "", "metadata": metadata or {} }

        if entity_to_stop.has_attribute("checklist"):
            self.logger.info(f"Entity '{entity_to_stop.get_identifier()}' has a checklist. Processing for smart defaults.")
            checklist_tv = entity_to_stop.get_attribute_typed("checklist")
            if checklist_tv and isinstance(checklist_tv.value, list):
                
                updated_checklist_items = [] 
                
                for item_hy_dict in checklist_tv.value:
                    py_dict = {}
                    if isinstance(item_hy_dict, list):
                        py_dict = list_to_dict(item_hy_dict)
                    elif isinstance(item_hy_dict, (hy.models.Dict, hy.models.Expression)):
                        py_dict = list_to_dict(converter.model_to_py(item_hy_dict), raw=True)
                    else:
                        updated_checklist_items.append(item_hy_dict) 
                        continue
                    
                    is_mandatory = str(py_dict.get("is_mandatory")).lower() == 'true'
                    is_completed = str(py_dict.get("completed")).lower() == 'true'

                    if is_mandatory and not is_completed:
                        step_name = py_dict.get('name', 'unnamed_step')
                        self.logger.info(f"Auto-completing mandatory step: {step_name}")
                        
                        py_dict['completed'] = True
                        
                        action_as_list = py_dict.get("default_action")
                        if isinstance(action_as_list, list) and len(action_as_list) > 0:
                            action_to_run = converter.py_to_model(action_as_list)
                            self.logger.info(f"Executing default action for: {step_name}")
                            try:
                                self._loader._dynamic_service.evaluate(
                                    expression=action_to_run, context={"self": entity_to_stop},
                                    component_type="checklist_action",
                                    component_label=f"{entity_to_stop.get_identifier()}:{step_name}",
                                    attribute="default_action"
                                )
                            except Exception as e:
                                self.logger.error(f"Failed to run default action for '{step_name}': {e}")
                    updated_checklist_items.append(converter.py_to_model(py_dict))
                checklist_tv.value = updated_checklist_items

        occurrences_tv = entity_to_stop.get_attribute_typed(list_attribute_name)
        if not occurrences_tv:
            occurrences_tv = TypedValue(value=[], field_type=FieldType.LIST, item_schema_type="OCCURRENCE")
            entity_to_stop.set_attribute_typed(list_attribute_name, occurrences_tv)
        
        current_list = []
        if isinstance(occurrences_tv.value, list):
            for item in occurrences_tv.value:
                if isinstance(item, hy.models.Object):
                    current_list.append(item)
                elif isinstance(item, dict):
                    current_list.append(converter.py_to_model(item))
        new_occurrence_hy_dict = converter.py_to_model(new_occurrence_data)
        new_list = current_list + [new_occurrence_hy_dict]
        occurrences_tv.value = new_list 

        cleared_start_time_tv = TypedValue(value=None, field_type=FieldType.DATETIME, original="None")
        entity_to_stop.set_attribute_typed(active_start_time_attr, cleared_start_time_tv)
        self._entity_manager.release_claims(entity_to_stop)

        entity_id = entity_to_stop.get_identifier()
        self.logger.info(f"Ended and logged occurrence for '{entity_id}' in memory.")
        self._run_hook_code(entity_to_stop, "on_end_hook", "end")
        self._save_entities_in_category(entity_to_stop.entity_type, entity_to_stop.category)
        return entity_to_stop


    def toggle_checklist_step(self, entity_type: str, category: str, name: str, step_name: str, new_status: bool) -> Entity:
        entity = self.get_entity(entity_type, category, name)
        if not entity: raise ValueError(f"Entity '{entity_type}:{category}:{name}' not found.")
        if not entity.get_attribute_value("active_occurrence_start_time"): raise ValueError(f"Entity '{name}' does not have an active occurrence.")

        checklist_tv = entity.get_attribute_typed("checklist")
        if not checklist_tv or not isinstance(checklist_tv.value, list): raise TypeError(f"Entity '{name}' does not have a valid 'checklist' attribute.")

        mutable_checklist = checklist_tv.value
        item_found = False
        action_to_run = None

        for item_dict in mutable_checklist:
            if isinstance(item_dict, dict) and item_dict.get("name") == step_name:
                item_dict['completed'] = new_status
                item_found = True
                self.logger.info(f"Updated step '{step_name}' in memory for '{entity.get_identifier()}' to completed={new_status}.")

                if new_status and "default_action" in item_dict:
                    action_as_list = item_dict.get("default_action")

                    if isinstance(action_as_list, list):
                        try:
                            action_to_run = py_list_to_hy_expression(action_as_list)
                        except Exception as e:
                            self.logger.error(f"Could not convert default_action list to expression: {e}")
                break

        if not item_found:
            raise ValueError(f"Step '{step_name}' not found in the checklist for entity '{name}'.")

        self._save_entities_in_category(entity.entity_type, entity.category)

        if action_to_run:
            self.logger.info(f"Executing action for completing step '{step_name}': {hy.repr(action_to_run)}")
            try:
                self._loader._dynamic_service.evaluate(
                    expression=action_to_run, 
                    context={"self": entity},
                    component_type="checklist_action",
                    component_label=f"{entity.get_identifier()}:{step_name}",
                    attribute="default_action"
                )
            except Exception as e:
                self.logger.error(f"Action for step '{step_name}' failed: {e}. Reverting completed status.")
                for item_dict in mutable_checklist:
                    if item_dict.get("name") == step_name:
                        item_dict['completed'] = not new_status
                        break
                self._save_entities_in_category(entity.entity_type, entity.category)
                raise e

        return entity

    def _run_hook_code(self, entity: Entity, hook_attribute_name: str, event_name: str):
        """
        Finds and executes the Hy code defined in a hook attribute on an entity.
        """
        self.logger.debug(
            f"Checking for '{hook_attribute_name}' on '{entity.name}' for '{event_name}' event."
        )
        hook_tv = entity.get_attribute_typed(hook_attribute_name)

        if not hook_tv or not hook_tv.original:
            self.logger.debug(f"No hook expression defined for this event.")
            return

        hook_expression = hook_tv.value
        if not (isinstance(hook_expression, hy.models.Expression) and str(hook_expression[0]) == "quote"):
            self.logger.warning(f"Hook '{hook_attribute_name}' on '{entity.name}' is not a quoted expression. Skipping.")
            return
        code_to_run = hook_expression[1] 
        self.logger.info(f"Executing '{event_name}' hook for '{entity.name}': {hy.repr(code_to_run)}")

        try:
            hook_context = {"self": entity}

            _, _ = self._loader._dynamic_service.evaluate(
                expression=code_to_run,
                context=hook_context,
                component_type="entity_hook",
                component_label=entity.get_identifier(),
                attribute=hook_attribute_name,
            )
            self.logger.info(f"Successfully executed '{event_name}' hook for '{entity.name}'.")

        except Exception as e:
            self.logger.error(
                f"Error executing '{hook_attribute_name}' for entity '{entity.name}': {e}",
                exc_info=True,
            )

    def log_metric(
        self,
        category: str,
        name: str,
        value: Any,
        notes: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> Entity:
        """
        Logs a new point-in-time entry for a METRIC entity.

        This method handles validation of the incoming value against the metric's
        defined `metric_type`.
        """
        self.logger.debug(f"Attempting to log entry for metric '{category}:{name}' with value '{value}'")
        entity_type = "metric" 

        metric_entity = self.get_entity(entity_type, category, name)
        if not metric_entity:
            raise ValueError(f"Metric not found: {entity_type}:{category}:{name}")

        defined_type_str = metric_entity.get_attribute_value("metric_type")
        if not defined_type_str:
            raise TypeError(f"Metric '{name}' does not have a 'metric_type' defined and cannot be logged against.")

        is_valid = False
        if defined_type_str == "decimal":
            is_valid = isinstance(value, (float, int, Decimal))
        elif defined_type_str == "integer":
            is_valid = isinstance(value, int)
        elif defined_type_str == "boolean":
            is_valid = isinstance(value, bool)
        elif defined_type_str == "string":
            is_valid = isinstance(value, str)

        if not is_valid:
            raise ValueError(
                f"Invalid value '{value}' (type: {type(value).__name__}) for metric '{name}'. "
                f"This metric expects a '{defined_type_str}'."
            )

        from utms.utils import get_ntp_date
        
        entry_timestamp = timestamp if timestamp else get_ntp_date()

        new_entry = {
            "timestamp": entry_timestamp,
            "value": value,
            "notes": notes or "",
        }

        entries_tv = metric_entity.get_attribute_typed("entries")
        if not entries_tv:
             entries_tv = TypedValue(
                value=[], field_type=FieldType.LIST, item_schema_type="METRIC_ENTRY"
            )
             metric_entity.set_attribute_typed("entries", entries_tv)

        raw_current_list = entries_tv.value if isinstance(entries_tv.value, list) else []
        sanitized_current_list = []
        for item in raw_current_list:
            if isinstance(item, dict):
                pure_py_dict = { str(k).lstrip(':'): v for k, v in item.items() }
                sanitized_current_list.append(pure_py_dict)
        entry_timestamp = timestamp if timestamp else get_ntp_date()

        new_entry = {
            "timestamp": entry_timestamp,
            "value": value,
            "notes": notes or "",
        }

        new_list = sanitized_current_list + [new_entry]
        entries_tv.value = new_list
        entries_tv.original = converter.py_to_string(new_list)
        self.logger.info(f"Logged new entry for metric '{name}': {new_entry}")
        self._save_entities_in_category(metric_entity.entity_type, metric_entity.category)
        return metric_entity

    def remove_metric_entry(self, category: str, name: str, timestamp_iso: str) -> Entity:
        """
        Removes a specific entry from a METRIC's entries list, identified by its ISO timestamp.
        """
        self.logger.debug(f"Attempting to remove entry from metric '{category}:{name}' at time '{timestamp_iso}'")
        entity_type = "metric"

        metric_entity = self.get_entity(entity_type, category, name)
        if not metric_entity:
            raise ValueError(f"Metric not found: {entity_type}:{category}:{name}")

        entries_tv = metric_entity.get_attribute_typed("entries")
        if not entries_tv or not isinstance(entries_tv.value, list):
            raise ValueError(f"No entries found for metric '{name}' to remove from.")

        try:
            target_ts = datetime.fromisoformat(timestamp_iso.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError(f"Invalid timestamp format: '{timestamp_iso}'. Please use ISO 8601 format.")

        original_list = entries_tv.value
        new_list = [
            entry for entry in original_list
            if not (
                isinstance(entry.get("timestamp"), datetime) and
                entry.get("timestamp").isoformat() == target_ts.isoformat()
            )
        ]

        if len(new_list) == len(original_list):
            raise ValueError(f"No entry found with timestamp '{timestamp_iso}' for metric '{name}'.")

        entries_tv.value = new_list
        entries_tv.original = converter.py_to_string(new_list)

        self.logger.info(f"Removed entry at {timestamp_iso} from metric '{name}'.")

        self._save_entities_in_category(metric_entity.entity_type, metric_entity.category)

        return metric_entity    

    def start_timer(self, category: str, name: str) -> Entity:
        entity = self.get_entity("timer", category, name)
        if not entity:
            raise ValueError(f"Timer 'timer:{category}:{name}' not found.")

        status = entity.get_attribute_value("status")
        if status == "running":
            raise ValueError("Timer is already running.")

        now = datetime.now()

        if status == "paused":
            remaining_seconds = entity.get_attribute_value("remaining_at_pause", 0)
            new_end_time = now + timedelta(seconds=remaining_seconds)
            self.update_entity_attribute("timer", category, name, "end_time", new_end_time)
            self.update_entity_attribute("timer", category, name, "remaining_at_pause", None) 
        else: 
            duration_seconds = entity.get_attribute_value("duration_seconds")
            if not duration_seconds:
                raise ValueError("Timer has no duration_seconds set.")
            new_end_time = now + timedelta(seconds=duration_seconds)
            self.update_entity_attribute("timer", category, name, "end_time", new_end_time)
            self.update_entity_attribute("timer", category, name, "finish_cursor", None) 

        self.update_entity_attribute("timer", category, name, "status", "running")
        return self.get_entity("timer", category, name)


    def pause_timer(self, category: str, name: str) -> Entity:
        entity = self.get_entity("timer", category, name)
        if not entity:
            raise ValueError(f"Timer 'timer:{category}:{name}' not found.")

        status = entity.get_attribute_value("status")
        if status != "running":
            raise ValueError("Timer is not running, cannot pause.")

        now = datetime.now()
        end_time = entity.get_attribute_value("end_time")

        if not isinstance(end_time, datetime):
            raise TypeError("Timer end_time is not a valid datetime.")

        remaining_seconds = max(0, (end_time - now).total_seconds())

        self.update_entity_attribute("timer", category, name, "status", "paused")
        self.update_entity_attribute("timer", category, name, "pause_time", now)
        self.update_entity_attribute("timer", category, name, "remaining_at_pause", int(remaining_seconds))

        return self.get_entity("timer", category, name)


    def reset_timer(self, category: str, name: str) -> Entity:
        entity = self.get_entity("timer", category, name)
        if not entity:
            raise ValueError(f"Timer 'timer:{category}:{name}' not found.")

        self.update_entity_attribute("timer", category, name, "status", "idle")
        self.update_entity_attribute("timer", category, name, "end_time", None)
        self.update_entity_attribute("timer", category, name, "pause_time", None)
        self.update_entity_attribute("timer", category, name, "remaining_at_pause", None)
        self.update_entity_attribute("timer", category, name, "finish_cursor", None)

        return self.get_entity("timer", category, name)    
