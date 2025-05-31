# utms.core.components.elements.time_entity.py
import os
from typing import Any, Dict, List, Optional, Union

import hy # For hy.read in save, if needed

from utms.core.components.base import SystemComponent
from utms.core.hy.ast import HyAST
from utms.core.loaders.base import LoaderContext
from utms.core.loaders.elements.time_entity import TimeEntityLoader # Updated loader
from utms.core.managers.elements.time_entity import TimeEntityManager # Updated manager
from utms.core.models.elements.time_entity import TimeEntity # Updated model
from utms.core.plugins import plugin_registry
from utms.core.plugins.elements.dynamic_time_entity import plugin_generator # Updated generator/plugin
from utms.utils import hy_to_python, list_to_dict # list_to_dict for schema processing

# Import TypedValue and related types
from utms.utms_types.field.types import TypedValue, FieldType, infer_type
from utms.utms_types import HyNode # For type hinting if HyNodes are directly handled


class TimeEntityComponent(SystemComponent):
    """Component managing UTMS time entities with TypedValue attributes."""

    def __init__(self, config_dir: str, component_manager=None):
        super().__init__(config_dir, component_manager)
        self._ast_manager = HyAST()
        # Manager now expects TimeEntity with attributes: Dict[str, TypedValue]
        self._time_entity_manager = TimeEntityManager() 
        # Loader now produces TimeEntity with attributes: Dict[str, TypedValue]
        self._loader = TimeEntityLoader(self._time_entity_manager)
        self._entities_dir = os.path.join(self._config_dir, "entities") # For entity type definitions
        self._entity_base_dir = self._config_dir # For type-specific dirs like 'tasks/', 'events/'
        
        # self.entity_types stores schema: Dict[str_entity_type_lowercase, EntitySchemaDict]
        # EntitySchemaDict is like: {"name": "TASK", "attributes_schema": {"desc": {"type": "string", ...}}}
        self.entity_types: Dict[str, Dict[str, Any]] = {} 
        self._items = self._time_entity_manager._items # Direct access for unified item storage

    def load(self) -> None:
        """Load entity type definitions and then entity instances."""
        if self._loaded:
            self.logger.debug("TimeEntityComponent already loaded.")
            return
        self.logger.info("Loading Time Entities...")

        if not os.path.exists(self._entities_dir):
            os.makedirs(self._entities_dir)
        if not os.path.exists(self._entity_base_dir): # Should be same as config_dir
            os.makedirs(self._entity_base_dir)

        try:
            variables_component = self.get_component("variables")
            variables = {}
            if variables_component:
                # Assuming variables_component.items() returns name -> VariableModel
                # And VariableModel.value is a TypedValue whose .value is resolved.
                for name, var_model in variables_component.items():
                    try:
                        # Ensure var_model.value is a TypedValue and we get its Python value
                        var_typed_value = var_model.value 
                        if isinstance(var_typed_value, TypedValue):
                            py_val = var_typed_value.value
                        else: # Fallback if VariableComponent doesn't use TypedValue yet
                            py_val = hy_to_python(var_model) # Or var_model.get_value()
                        
                        variables[name] = py_val
                        variables[name.replace("-", "_")] = py_val
                    except Exception as e:
                        self.logger.error(f"Error processing variable '{name}': {e}", exc_info=True)
            self.logger.debug(f"Context variables for entity loading: {list(variables.keys())}")
            context = LoaderContext(config_dir=self._config_dir, variables=variables)

            # 1. Load Entity Type Definitions first (from _entities_dir/entity_types.hy)
            entity_types_file = os.path.join(self._entities_dir, "entity_types.hy")
            if os.path.exists(entity_types_file):
                self.logger.debug(f"Loading entity type definitions from: {entity_types_file}")
                type_def_nodes = self._ast_manager.parse_file(entity_types_file)
                # The loader doesn't process "def-time-entity" nodes into TimeEntity *instances*.
                # We extract schema from these nodes directly.
                self._extract_entity_types_from_nodes(type_def_nodes)
            else:
                self.logger.warning(f"Entity types definition file not found: {entity_types_file}")

            # 2. Generate and register plugins for discovered entity types
            if self.entity_types:
                self._register_entity_type_plugins()
            else:
                self.logger.info("No entity types defined. Skipping instance loading from type directories.")
                self._loaded = True
                return

            # 3. Load entity instances from type-specific directories (e.g., tasks/, events/)
            self._load_entities_from_type_dirs(context)
            
            self._loaded = True
            self.logger.info(f"Time Entities loading complete. Loaded {len(self._items)} instances.")

        except Exception as e:
            self.logger.error(f"Fatal error during TimeEntityComponent load: {e}", exc_info=True)
            # Depending on severity, you might want to clear self._items or re-raise
            self._loaded = False # Mark as not successfully loaded
            raise

    def _extract_entity_types_from_nodes(self, type_def_nodes: List[HyNode]) -> None:
        """
        Extract entity type schemas from HyNodes parsed by TimeEntityNodePlugin
        (from entity_types.hy).
        """
        self.entity_types = {} # Reset
        self.logger.debug(f"Extracting entity types from {len(type_def_nodes)} definition nodes.")
        for node in type_def_nodes:
            if node.type != "def-time-entity": # Parsed by TimeEntityNodePlugin
                self.logger.warning(f"Unexpected node type '{node.type}' in entity_types.hy, expected 'def-time-entity'.")
                continue

            # node.value is display_name (e.g., "TASK")
            # node.definition_kind should be "entity-type"
            # node.attribute_schemas_raw_hy is Dict[str, hy.models.HyObject (typically Dict)]
            
            display_name = str(node.value)
            definition_kind = getattr(node, "definition_kind", None)

            if definition_kind != "entity-type":
                self.logger.warning(
                    f"Skipping def-time-entity '{display_name}' with kind '{definition_kind}'. "
                    f"Expected 'entity-type'."
                )
                continue

            entity_type_key = display_name.lower() # e.g., "task"
            
            raw_hy_attr_schemas: Dict[str, hy.models.HyObject] = getattr(node, "attribute_schemas_raw_hy", {})
            processed_py_attr_schemas: Dict[str, Dict[str, Any]] = {}

            for attr_name_str, attr_schema_hy_dict in raw_hy_attr_schemas.items():
                if not isinstance(attr_schema_hy_dict, hy.models.Dict):
                    self.logger.warning(
                        f"Attribute schema for '{attr_name_str}' of entity type '{display_name}' "
                        f"is not a Hy Dict as expected: {type(attr_schema_hy_dict)}. Skipping attribute."
                    )
                    continue
                
                # Convert Hy Dict like {:type "string" ...} to Python Dict
                try:
                    # hy_to_python on a Hy Dict returns a list of pairs: [:key1, val1, :key2, val2]
                    py_schema_list_of_pairs = hy_to_python(attr_schema_hy_dict)
                    # list_to_dict converts this flat list into a Python dict
                    py_schema_dict = list_to_dict(py_schema_list_of_pairs)
                    # Ensure keys are strings if they were keywords
                    py_schema_final = {str(k): v for k, v in py_schema_dict.items()}
                    processed_py_attr_schemas[attr_name_str] = py_schema_final
                except Exception as e_conv:
                    self.logger.error(
                        f"Error converting schema for attribute '{attr_name_str}' of type '{display_name}': {e_conv}",
                        exc_info=True
                    )
                    continue
            
            self.entity_types[entity_type_key] = {
                "name": display_name, # User-friendly display name, e.g., "TASK"
                "attributes_schema": processed_py_attr_schemas, # Python dict of schema details
            }
            self.logger.info(f"Extracted schema for entity type '{entity_type_key}' (Display: '{display_name}')")
            self.logger.debug(f"  Schema for '{entity_type_key}': {processed_py_attr_schemas}")


    def _register_entity_type_plugins(self) -> None:
        """Generate and register instance parser plugins for defined entity types."""
        if not self.entity_types:
            self.logger.debug("No entity types defined, skipping plugin registration.")
            return
            
        self.logger.debug(f"Registering instance parser plugins for {len(self.entity_types)} entity types.")
        for entity_type_key, schema_definition in self.entity_types.items():
            # entity_type_key is lowercase, e.g., "task"
            # schema_definition["attributes_schema"] is Dict[str, PythonDict_of_attr_schema_details]
            try:
                attributes_schema_for_plugin = schema_definition.get("attributes_schema", {})
                
                # plugin_generator is the singleton from dynamic_time_entity.py
                # It generates classes like TaskInstanceParserPlugin
                plugin_class = plugin_generator.generate_plugin(
                    entity_type_name_str=entity_type_key, # e.g., "task"
                    attributes_schema_for_type=attributes_schema_for_plugin
                )
                # Registers the *class*, not an instance. HyAST will instantiate it.
                plugin_registry.register_node_plugin(plugin_class) 
                self.logger.debug(
                    f"Successfully registered plugin '{plugin_class.__name__}' "
                    f"for node_type 'def-{entity_type_key}'."
                )
            except Exception as e:
                self.logger.error(
                    f"Error generating or registering plugin for entity type '{entity_type_key}': {e}",
                    exc_info=True
                )

    def _load_entities_from_type_dirs(self, context: LoaderContext) -> None:
        """Load entity instances from type-specific directories (e.g., tasks/, events/)."""
        if not self.entity_types:
            self.logger.debug("No entity types available to load instances for.")
            return

        self.logger.debug("Loading entity instances from type-specific directories...")
        total_instances_loaded = 0
        for entity_type_key in self.entity_types.keys(): # e.g., "task"
            # Directory name is plural, e.g., tasks, events
            type_specific_dir = os.path.join(self._entity_base_dir, f"{entity_type_key}s")
            
            self.logger.debug(f"Checking for instance directory for type '{entity_type_key}': {type_specific_dir}")
            if not os.path.isdir(type_specific_dir):
                self.logger.debug(f"Directory not found or not a directory: {type_specific_dir}. Skipping.")
                # Optionally create it: os.makedirs(type_specific_dir, exist_ok=True)
                continue

            hy_files_in_dir = [f for f in os.listdir(type_specific_dir) if f.endswith(".hy")]
            if not hy_files_in_dir:
                self.logger.debug(f"No .hy files found in {type_specific_dir}.")
                continue
            
            self.logger.info(f"Loading instances for type '{entity_type_key}' from {type_specific_dir} ({len(hy_files_in_dir)} files).")

            for filename in hy_files_in_dir:
                filepath = os.path.join(type_specific_dir, filename)
                self.logger.debug(f"  Processing instance file: {filepath}")
                try:
                    # HyAST uses plugin_registry to find the correct plugin (e.g., TaskInstanceParserPlugin)
                    # based on the S-expression leader (e.g., def-task).
                    instance_nodes = self._ast_manager.parse_file(filepath)
                    if not instance_nodes:
                        self.logger.debug(f"    No nodes parsed from {filepath}.")
                        continue
                    
                    self.logger.debug(f"    Parsed {len(instance_nodes)} nodes from {filepath}.")
                    
                    # self._loader is TimeEntityLoader. Its process method now handles
                    # HyNodes with "attributes_typed" and "entity_type_name_str",
                    # resolves dynamic values, and creates TimeEntity instances
                    # with finalized Dict[str, TypedValue] attributes.
                    # These are added to self._time_entity_manager._items.
                    loaded_instances_from_file = self._loader.process(instance_nodes, context)
                    total_instances_loaded += len(loaded_instances_from_file)
                    self.logger.debug(
                        f"    Successfully processed {len(loaded_instances_from_file)} entity instances from {filepath}."
                    )
                except Exception as e_file:
                    self.logger.error(f"  Error loading entity instances from {filepath}: {e_file}", exc_info=True)
                    # Continue with other files

        self.logger.debug(f"Finished loading from type directories. Total new instances: {total_instances_loaded}")


    def save(self) -> None:
        """Save entity type definitions and entity instances to appropriate .hy files."""
        self.logger.info("Saving Time Entities...")

        # 1. Save Entity Type Definitions (to _entities_dir/entity_types.hy)
        if not os.path.exists(self._entities_dir):
            os.makedirs(self._entities_dir)
        
        entity_types_file = os.path.join(self._entities_dir, "entity_types.hy")
        schema_plugin = plugin_registry.get_node_plugin("def-time-entity") # TimeEntityNodePlugin
        if not schema_plugin:
            self.logger.error("TimeEntityNodePlugin (for 'def-time-entity') not found. Cannot save schemas.")
            # Potentially raise error or return
        else:
            type_def_hy_lines = []
            # self.entity_types is Dict[str_lowercase_type, {"name": "DISPLAY_NAME", "attributes_schema": ...}]
            sorted_entity_type_keys = sorted(self.entity_types.keys())

            for entity_type_key in sorted_entity_type_keys:
                schema_def = self.entity_types[entity_type_key]
                display_name = schema_def["name"] # e.g., "TASK"
                # attributes_schema is Dict[str_attr_name, PythonDict_attr_schema_details]
                python_attr_schemas = schema_def["attributes_schema"] 

                # Reconstruct attribute_schemas_raw_hy (Dict[str, hy.models.Dict]) for formatting
                # This is because TimeEntityNodePlugin.format expects node.attribute_schemas_raw_hy
                attr_schemas_for_hy_node: Dict[str, hy.models.HyObject] = {}
                for attr_name, py_schema_dict in python_attr_schemas.items():
                    # Convert Python dict schema back to Hy Dict. This is a bit tricky.
                    # hy.⁂(...) can construct Hy data structures from Python.
                    # Example: hy.⁂({hy.Keyword('type'): "string"}) creates <HyDict {Keyword('type'): <HyString 'string'>}>
                    hy_dict_elements = []
                    for k, v in py_schema_dict.items():
                        hy_dict_elements.append(hy.Keyword(k))
                        # format_value should ideally handle Python types to Hy objects for hy.⁂
                        # but hy.⁂ expects Hy objects directly if possible.
                        # For simplicity, we assume string keys and basic value types here.
                        # A more robust Python-to-Hy converter might be needed if schemas are complex.
                        if isinstance(v, str): hy_dict_elements.append(hy.models.String(v))
                        elif isinstance(v, int): hy_dict_elements.append(hy.models.Integer(v))
                        elif isinstance(v, bool): hy_dict_elements.append(hy.models.Boolean(v))
                        elif isinstance(v, list): # Simple list of strings/numbers for enum_choices
                            hy_list_items = []
                            for item in v:
                                if isinstance(item, str): hy_list_items.append(hy.models.String(item))
                                elif isinstance(item, int): hy_list_items.append(hy.models.Integer(item))
                                else: hy_list_items.append(hy.models.String(str(item))) # Fallback
                            hy_dict_elements.append(hy.models.List(hy_list_items))
                        else: hy_dict_elements.append(hy.models.String(str(v))) # Fallback

                    attr_schemas_for_hy_node[attr_name] = hy.models.List(hy_dict_elements).as_dict()


                # Create a mock HyNode suitable for schema_plugin.format
                node_for_formatting = HyNode(
                    type="def-time-entity",
                    value=display_name, # "TASK"
                    original=None # Not strictly needed for formatting from data
                )
                setattr(node_for_formatting, "definition_kind", "entity-type")
                setattr(node_for_formatting, "attribute_schemas_raw_hy", attr_schemas_for_hy_node)
                
                type_def_hy_lines.extend(schema_plugin.format(node_for_formatting))
                type_def_hy_lines.append("") # Blank line separator
            
            try:
                with open(entity_types_file, "w") as f:
                    f.write("\n".join(type_def_hy_lines))
                self.logger.info(f"Saved {len(self.entity_types)} entity type definitions to {entity_types_file}")
            except Exception as e_save_schema:
                self.logger.error(f"Error saving entity type definitions to {entity_types_file}: {e_save_schema}", exc_info=True)


        # 2. Save Entity Instances (to type-specific directories like tasks/default.hy)
        # Group current _items (TimeEntity instances) by their entity_type_str
        instances_by_type: Dict[str, List[TimeEntity]] = {}
        for entity_key, entity_instance in self._items.items():
            # Skip schema definitions if they were in _items (they shouldn't be based on loader logic)
            # entity_instance.entity_type is like "task" (lowercase from model)
            type_key = entity_instance.entity_type 
            if type_key not in instances_by_type:
                instances_by_type[type_key] = []
            instances_by_type[type_key].append(entity_instance)

        for entity_type_key, instances_list in instances_by_type.items():
            # entity_type_key is "task", "event", etc.
            instance_plugin_node_type = f"def-{entity_type_key}" # e.g., "def-task"
            instance_plugin = plugin_registry.get_node_plugin(instance_plugin_node_type)

            if not instance_plugin:
                self.logger.warning(
                    f"No instance parser plugin found for node_type '{instance_plugin_node_type}'. "
                    f"Cannot save instances of type '{entity_type_key}'."
                )
                continue

            # Determine save directory (e.g., /config/tasks/)
            type_specific_dir = os.path.join(self._entity_base_dir, f"{entity_type_key}s")
            if not os.path.exists(type_specific_dir):
                os.makedirs(type_specific_dir)
            
            # For now, save all instances of a type to a "default.hy" file within their type directory
            instance_file_path = os.path.join(type_specific_dir, "default.hy")
            instance_hy_lines = []

            sorted_instances = sorted(instances_list, key=lambda inst: inst.name)

            for entity_instance in sorted_instances:
                # entity_instance.attributes is Dict[str, TypedValue]
                # The instance_plugin.format method expects a HyNode with 'attributes_typed'
                
                # Create a HyNode suitable for the instance_plugin.format method
                node_for_formatting = HyNode(
                    type=instance_plugin_node_type, # e.g., "def-task"
                    value=entity_instance.name, # Instance name
                    original=None # Not strictly needed for formatting from data
                )
                # The plugin's format method expects 'attributes_typed' to be Dict[str, TypedValue]
                setattr(node_for_formatting, "attributes_typed", entity_instance.get_all_attributes_typed())
                # entity_type_name_str might also be useful if format needs it, though node.type has it.
                # setattr(node_for_formatting, "entity_type_name_str", entity_instance.entity_type)

                instance_hy_lines.extend(instance_plugin.format(node_for_formatting))
                instance_hy_lines.append("") # Blank line separator
            
            try:
                with open(instance_file_path, "w") as f:
                    f.write("\n".join(instance_hy_lines))
                self.logger.info(
                    f"Saved {len(instances_list)} instances of type '{entity_type_key}' to {instance_file_path}"
                )
            except Exception as e_save_inst:
                self.logger.error(
                    f"Error saving '{entity_type_key}' instances to {instance_file_path}: {e_save_inst}", 
                    exc_info=True
                )
        self.logger.info("Time Entities saving complete.")

    # --- CRUD-like and Helper Methods ---

    def _get_entity_schema(self, entity_type_str: str) -> Optional[Dict[str, Any]]:
        """Helper to get the attribute schema for a given entity type."""
        type_def = self.entity_types.get(entity_type_str.lower())
        if type_def:
            return type_def.get("attributes_schema")
        return None

    def create_entity(
        self,
        name: str,
        entity_type: str, # lowercase string like "task"
        attributes_raw: Optional[Dict[str, Any]] = None, # Raw Python values from API/user
        # No explicit dynamic_fields; is_dynamic is per attribute TypedValue
    ) -> TimeEntity:
        """
        Create a new time entity from raw attribute values.
        This method will construct TypedValue objects for each attribute.
        """
        self.logger.debug(f"Component.create_entity: name='{name}', type='{entity_type}', raw_attrs='{attributes_raw}'")
        entity_type_key = entity_type.lower()
        schema = self._get_entity_schema(entity_type_key)
        if not schema:
            # Allow creation even if schema is missing, but types will be inferred.
            self.logger.warning(
                f"No schema found for entity type '{entity_type_key}' during create_entity. "
                f"Attribute types will be inferred."
            )
            schema = {}

        final_typed_attributes: Dict[str, TypedValue] = {}
        raw_attributes_to_process = attributes_raw or {}

        for attr_name, raw_value in raw_attributes_to_process.items():
            attr_schema_details = schema.get(attr_name, {})
            
            # Determine FieldType, item_type, enum_choices from schema or infer
            declared_type_str = attr_schema_details.get("type")
            field_type_enum = FieldType.from_string(declared_type_str) if declared_type_str else infer_type(raw_value)
            
            item_type_str = attr_schema_details.get("item_type")
            item_type_enum = FieldType.from_string(item_type_str) if item_type_str else None
            
            enum_choices = attr_schema_details.get("enum_choices", [])
            
            # For create_entity, assume values are static unless 'raw_value' is an expression string
            is_dynamic = False
            original_expr = None
            current_value_for_typed_value = raw_value

            if isinstance(raw_value, str) and raw_value.strip().startswith("(") and field_type_enum == FieldType.CODE:
                # If it looks like a Hy expression and type is CODE, treat as dynamic
                is_dynamic = True
                original_expr = raw_value
                # For dynamic code, the loader would resolve it. Here, we store the code string.
                # TypedValue with FieldType.CODE stores the string.
                # Or, if you want create_entity to resolve immediately:
                # resolved_val, _ = self._dynamic_service.evaluate(...)
                # current_value_for_typed_value = resolved_val
                # For now, let's assume create_entity doesn't auto-resolve for simplicity,
                # it just sets up the TypedValue. Resolution happens on load or explicit call.
                # This matches how config items with expressions are handled.
            
            final_typed_attributes[attr_name] = TypedValue(
                value=current_value_for_typed_value,
                field_type=field_type_enum,
                is_dynamic=is_dynamic,
                original=original_expr,
                enum_choices=enum_choices,
                item_type=item_type_enum
            )
        
        # Call manager's create, which now expects Dict[str, TypedValue]
        entity_instance = self._time_entity_manager.create(
            name=name,
            entity_type=entity_type_key,
            attributes=final_typed_attributes,
        )
        # self._items is already updated by the manager's add method.
        self.save() # Persist changes
        return entity_instance

    def get_entity(self, entity_type: str, name: str) -> Optional[TimeEntity]:
        """Get a specific entity by type (lowercase string) and name."""
        return self._time_entity_manager.get_by_name_and_type(name, entity_type.lower())

    def get_by_type(self, entity_type: str) -> List[TimeEntity]:
        """Get all entities of a specific type (lowercase string)."""
        return self._time_entity_manager.get_by_type(entity_type.lower())

    def remove_entity(self, entity_type: str, name: str) -> None:
        """Remove a time entity by type (lowercase string) and name."""
        key = f"{entity_type.lower()}:{name}"
        if key in self._items: # _items is self._time_entity_manager._items
            self._time_entity_manager.remove(key)
            self.save()
        else:
            self.logger.warning(f"Entity not found for removal: type='{entity_type}', name='{name}'")

    def get_entity_types(self) -> List[str]:
        """
        Get all registered entity type keys (lowercase strings like "task", "event").
        Ensures types are loaded if they haven't been.
        """
        if not self.entity_types and not self._loaded: # Check both if entity_types isn't populated
            self.logger.debug("Entity types not determined yet and component not loaded. Calling self.load().")
            self.load()
        elif not self.entity_types and self._loaded:
             self.logger.warning("Component loaded but no entity types found. This might indicate missing 'entity_types.hy' or empty definitions.")
        
        return list(self.entity_types.keys())


    def get_all_entity_type_details(self) -> List[Dict[str, Any]]:
        """
        Returns a list of dictionaries, each representing an entity type 
        with its name (key), displayName, and attribute schema, suitable for the frontend.
        """
        if not self.entity_types and not self._loaded: 
            self.logger.debug("Entity types schema info not available (component not loaded). Attempting load.")
            self.load() 
        
        details = []
        # self.entity_types is Dict[str_lowercase_type, {"name": "DISPLAY_NAME", "attributes_schema": PyDictSchema}]
        for type_key_lower, type_data_dict in self.entity_types.items():
            details.append({
                "name": type_key_lower, # e.g., "task"
                "displayName": type_data_dict.get("name", type_key_lower.upper()), # e.g., "TASK"
                "attributes": type_data_dict.get("attributes_schema", {}) 
            })
        self.logger.debug(f"Returning all entity type details ({len(details)} types).")
        return details


    def update_entity_attribute(
        self, 
        entity_type: str, 
        name: str, 
        attr_name: str, 
        new_raw_value: Any,
        # Optional: allow specifying if the new value is a dynamic expression
        is_new_value_dynamic: bool = False, 
        new_original_expression: Optional[str] = None
        ):
        """
        Update a specific entity attribute value.
        The new_raw_value is a Python value. If it's meant to be a dynamic expression,
        is_new_value_dynamic should be True and new_original_expression provided.
        """
        entity = self.get_entity(entity_type, name)
        if not entity:
            raise ValueError(f"Entity {entity_type}:{name} not found for update.")

        existing_typed_value = entity.get_attribute_typed(attr_name)
        
        schema = self._get_entity_schema(entity_type.lower()) or {}
        attr_schema_details = schema.get(attr_name, {})

        declared_type_str = attr_schema_details.get("type")
        item_type_str = attr_schema_details.get("item_type")
        enum_choices = attr_schema_details.get("enum_choices", [])

        field_type_enum: FieldType
        if existing_typed_value:
            field_type_enum = existing_typed_value.field_type # Prefer existing type
            if not item_type_str and existing_typed_value.item_type: # Preserve existing item_type
                item_type_str = str(existing_typed_value.item_type.value)
            if not enum_choices and existing_typed_value.enum_choices: # Preserve existing enum_choices
                enum_choices = existing_typed_value.enum_choices
        elif declared_type_str:
            field_type_enum = FieldType.from_string(declared_type_str)
        else:
            field_type_enum = infer_type(new_raw_value)
            
        item_type_enum = FieldType.from_string(item_type_str) if item_type_str else None

        # Handle if the update is to make it dynamic or change its expression
        if is_new_value_dynamic:
            if not new_original_expression or not new_original_expression.strip().startswith("("):
                raise ValueError("If 'is_new_value_dynamic' is True, 'new_original_expression' must be a valid Hy s-expression string.")
            # Value for TypedValue should be the code string itself if field_type is CODE,
            # or if it's another type, we might need to resolve it here or expect the API to send resolved.
            # For simplicity, if making it dynamic, the new_raw_value is often the original expression itself
            # or a placeholder if it needs immediate resolution.
            # Let's assume if making dynamic, new_raw_value IS the expression string, and type becomes CODE.
            # Or, if schema type is not CODE, new_raw_value is the *resolved* value of new_original_expression.
            # This needs to be clear for the API. For now, let's make TypedValue handle it.
            # If it's dynamic, field_type is often CODE, or schema_type if it's a dynamic value of that type.
            # If API sends resolved value for a new dynamic expression, that's fine.
            value_for_typed_value = new_raw_value
            if field_type_enum != FieldType.CODE and new_original_expression:
                 # If original expression is provided for a non-CODE field type,
                 # assume new_raw_value is the resolved version of that expression.
                 pass


            updated_typed_value = TypedValue(
                value=value_for_typed_value, # This could be the resolved value or the expression string
                field_type=field_type_enum, # Use schema-defined or inferred type
                is_dynamic=True,
                original=new_original_expression,
                enum_choices=enum_choices,
                item_type=item_type_enum
            )
        else: # Update is for a static value
            updated_typed_value = TypedValue(
                value=new_raw_value, # Raw Python value
                field_type=field_type_enum, # Use schema-defined or inferred type
                is_dynamic=False,
                original=None, # No original expression for static
                enum_choices=enum_choices,
                item_type=item_type_enum
            )
        
        entity.set_attribute_typed(attr_name, updated_typed_value)
        self.save()
        self.logger.info(f"Updated attribute '{attr_name}' for entity '{entity_type}:{name}'.")


    def rename_entity(self, entity_type: str, old_name: str, new_name: str):
        """Rename a time entity."""
        old_key = f"{entity_type.lower()}:{old_name}"
        new_key = f"{entity_type.lower()}:{new_name}"

        if old_key not in self._items:
            raise ValueError(f"Entity to rename not found: {old_key}")
        if new_key in self._items:
            raise ValueError(f"New entity name already exists: {new_key}")

        entity_to_rename = self._items.pop(old_key) # Remove from dict by old key
        entity_to_rename.name = new_name # Update the name property on the model
        self._items[new_key] = entity_to_rename # Re-add to dict with new key
        
        self.save()
        self.logger.info(f"Renamed entity from '{old_key}' to '{new_key}'.")


    def get_all_entity_type_details(self) -> List[Dict[str, Any]]:
        """
        Returns a list of dictionaries, each representing an entity type 
        with its name, display name, and attribute schema, suitable for the frontend.
        """
        if not self._loaded: # Ensure schemas are loaded
            self.logger.debug("Entity types schema info not available (component not loaded). Attempting load.")
            self.load() 
        
        # self.entity_types is Dict[str_lowercase_type, {"name": "DISPLAY_NAME", "attributes_schema": PyDictSchema}]
        details = []
        for type_key_lower, type_data_dict in self.entity_types.items():
            details.append({
                "name": type_key_lower, # e.g., "task"
                "displayName": type_data_dict.get("name", type_key_lower.upper()), # e.g., "TASK"
                # attributes_schema is already a Python Dict[str, PythonDict_of_schema_details]
                "attributes": type_data_dict.get("attributes_schema", {}) 
            })
        self.logger.debug(f"Returning all entity type details ({len(details)} types).")
        return details
    
    # Convenience getters for specific entity types can remain if useful,
    # they just call self.get_by_type()
    def get_tasks(self) -> List[TimeEntity]: return self.get_by_type("task")
    # ... and so on for other specific types like get_events, get_habits ...
