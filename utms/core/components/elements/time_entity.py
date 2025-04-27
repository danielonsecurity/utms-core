import os
from typing import Any, Dict, List, Optional, Union

import hy

from utms.core.components.base import SystemComponent
from utms.core.hy.ast import HyAST
from utms.core.loaders.base import LoaderContext
from utms.core.loaders.elements.time_entity import TimeEntityLoader
from utms.core.managers.elements.time_entity import TimeEntityManager
from utms.core.models.elements.time_entity import TimeEntity
from utms.core.plugins import plugin_registry
from utms.core.plugins.elements.dynamic_time_entity import plugin_generator
from utms.utils import hy_to_python


class TimeEntityComponent(SystemComponent):
    """Component managing UTMS time entities"""

    def __init__(self, config_dir: str, component_manager=None):
        super().__init__(config_dir, component_manager)
        self._ast_manager = HyAST()
        self._time_entity_manager = TimeEntityManager()
        self._loader = TimeEntityLoader(self._time_entity_manager)
        self._entities_dir = os.path.join(self._config_dir, "entities")
        self.entity_types = {}

    def load(self) -> None:
        """Load entities from all Hy files in the entities directory"""
        if self._loaded:
            return

        # Create entities directory if it doesn't exist
        if not os.path.exists(self._entities_dir):
            os.makedirs(self._entities_dir)
            
        try:
            # Get variables from variables component
            variables_component = self.get_component("variables")

            # Get resolved variable values
            variables = {}
            if variables_component:
                for name, var in variables_component.items():
                    try:
                        variables[name] = hy_to_python(var.value)
                        # Also add underscore version for compatibility
                        variables[name.replace("-", "_")] = hy_to_python(var.value)
                    except Exception as e:
                        self.logger.error(f"Error converting variable {name}: {e}")
                self.logger.debug(f"Available variables: {variables}")

            # Create context with variables
            context = LoaderContext(config_dir=self._config_dir, variables=variables)

            # Process all Hy files in the entities directory
            all_items = {}

            # Check if there are any files in the directory
            entities_files = [f for f in os.listdir(self._entities_dir) if f.endswith('.hy')]

            if not entities_files:
                self._loaded = True
                return

            for filename in entities_files:
                file_path = os.path.join(self._entities_dir, filename)
                self.logger.debug(f"Loading entities from {file_path}")

                try:
                    # Parse the file
                    nodes = self._ast_manager.parse_file(file_path)

                    # Process nodes using loader
                    items = self._loader.process(nodes, context)

                    # Add to all items
                    all_items.update(items)

                except Exception as e:
                    self.logger.error(f"Error loading entities from {file_path}: {e}")
                    # Continue with other files even if one fails

            self._items = all_items
            self._loaded = True
            
            # Extract entity types
            self._extract_entity_types()
            
            # Generate and register plugins for entity types
            self._register_entity_type_plugins()
            
            # Load entities from type-specific directories
            self._load_entities_from_type_dirs(context)

        except Exception as e:
            self.logger.error(f"Error loading entities: {e}")
            raise

    def _extract_entity_types(self) -> None:
        """Extract entity types from loaded entities."""
        for key, entity in self._items.items():
            if entity.entity_type == "entity-type":
                entity_type = entity.name.lower()
                
                # Store the entity type definition
                self.entity_types[entity_type] = {
                    "name": entity.name,
                    "attributes": entity.attributes
                }
                
                self.logger.debug(f"Extracted entity type: {entity_type}")

    def _register_entity_type_plugins(self) -> None:
        """Generate and register plugins for entity types."""
        for entity_type, info in self.entity_types.items():
            try:
                self.logger.debug("Generating plugin for entity type: %s", entity_type)
                self.logger.debug("Attributes: %s", info['attributes'])
                # Generate a plugin for this entity type
                plugin_class = plugin_generator.generate_plugin(
                    entity_type=entity_type,
                    attributes=info["attributes"]
                )
                self.logger.debug("Generated plugin class %s", plugin_class.__name__)
                # Register the plugin with the registry
                plugin_registry.register_node_plugin(plugin_class)
                registered_plugin = plugin_registry.get_node_plugin(f"def-{entity_type.lower()}")
                self.logger.debug("Registered plugin for def-%s: %s", entity_type.lower(), registered_plugin)
                self.logger.debug(f"Created and registered plugin for entity type: {entity_type}")
            except Exception as e:
                self.logger.error(f"Error creating plugin for entity type {entity_type}: {e}")

    def _load_entities_from_type_dirs(self, context: LoaderContext) -> None:
        """Load entities from type-specific directories."""
        # Load from each entity type directory
        self.logger.debug("Starting to load entities from type directories")
        for entity_type in self.entity_types:
            type_dir = os.path.join(self._config_dir, f"{entity_type}s")  # e.g., tasks, habits, events
            self.logger.debug("Checking directory for entity type %s: %s", entity_type, type_dir)
            if os.path.exists(type_dir):
                self.logger.debug(f"Loading entities from {type_dir}")
                
                # Get all .hy files in the directory
                hy_files = [f for f in os.listdir(type_dir) if f.endswith('.hy')]
                self.logger.debug(f"Found {len(hy_files)} .hy files: {hy_files}")
                
                for filename in hy_files:
                    filepath = os.path.join(type_dir, filename)
                    self.logger.debug(f"Processing file: {filepath}")
                    try:
                        self.logger.debug(f"Available plugins before parsing: {plugin_registry.list_node_plugins()}")
                        # Parse the file
                        nodes = self._ast_manager.parse_file(filepath)
                        self.logger.debug(f"Parsed {len(nodes)} nodes from {filepath}")
                        
                        # Process nodes using loader
                        items = self._loader.process(nodes, context)
                        self.logger.debug(f"Processed {len(items)} items from {filepath}")
                        
                        # Add to all items
                        self._items.update(items)
                        
                    except Exception as e:
                        self.logger.error(f"Error loading entities from {filepath}: {e}")
                        import traceback
                        self.logger.error(traceback.format_exc())

            else:
                self.logger.debug(f"Creating directory for entity type: {type_dir}")
                os.makedirs(type_dir, exist_ok=True)

    def save(self) -> None:
        """Save entities to appropriate files"""
        # Ensure entities directory exists
        if not os.path.exists(self._entities_dir):
            os.makedirs(self._entities_dir)

        # Get the time entity plugin
        plugin = plugin_registry.get_node_plugin("def-time-entity")
        if not plugin:
            raise ValueError("Time entity plugin not found")

        # Group entities by type
        entities_by_type = {}
        for key, entity in self._items.items():
            entity_type = entity.entity_type
            
            # Skip entity type definitions - they go in entities directory
            if entity_type == "entity-type":
                if "entity-types" not in entities_by_type:
                    entities_by_type["entity-types"] = []
                entities_by_type["entity-types"].append(entity)
                continue
                
            # Group by entity type
            if entity_type not in entities_by_type:
                entities_by_type[entity_type] = []
            entities_by_type[entity_type].append(entity)

        # Save entity type definitions to entities directory
        if "entity-types" in entities_by_type:
            file_path = os.path.join(self._entities_dir, "entity_types.hy")
            
            # Create nodes for each entity type definition
            lines = []
            for entity in sorted(entities_by_type["entity-types"], key=lambda e: e.name):
                # Create the entity definition expression
                node = plugin.parse(["def-time-entity", entity.name, entity.entity_type])
                
                # Add attributes to the node
                for attr_name, attr_value in entity.attributes.items():
                    if attr_name in entity.dynamic_fields and entity.dynamic_fields[attr_name].get('original'):
                        # For dynamic attributes, use the original expression
                        attr_expr = hy.read(entity.dynamic_fields[attr_name]['original'])
                    else:
                        # For static attributes, use the value
                        attr_expr = attr_value
                    
                    # Add attribute to node
                    node.attributes[attr_name] = attr_expr
                
                formatted_lines = plugin.format(node)
                lines.extend(formatted_lines)
                lines.append("")  # Add an empty line between entities
            
            # Write to file
            with open(file_path, "w") as f:
                f.write("\n".join(lines))
                
            self.logger.debug(f"Saved {len(entities_by_type['entity-types'])} entity type definitions to {file_path}")

        # Save entities to their type-specific directories
        for entity_type, entities in entities_by_type.items():
            if entity_type == "entity-types":
                continue  # Already handled
                
            # Get the appropriate plugin for this entity type
            type_plugin = plugin_registry.get_node_plugin(f"def-{entity_type}")
            if not type_plugin:
                self.logger.warning(f"No plugin found for entity type {entity_type}, using generic plugin")
                type_plugin = plugin
                
            # Create the type directory if it doesn't exist
            type_dir = os.path.join(self._config_dir, f"{entity_type}s")
            if not os.path.exists(type_dir):
                os.makedirs(type_dir)
                
            # Save to default file for this type
            file_path = os.path.join(type_dir, "default.hy")
            
            # Create nodes for each entity
            lines = []
            for entity in sorted(entities, key=lambda e: e.name):
                # Create the entity definition expression
                if type_plugin == plugin:
                    # Using generic plugin
                    node = plugin.parse(["def-time-entity", entity.name, entity.entity_type])
                else:
                    # Using specialized plugin
                    node = type_plugin.parse([f"def-{entity_type}", entity.name])
                
                # Add attributes to the node
                for attr_name, attr_value in entity.attributes.items():
                    if attr_name in entity.dynamic_fields and entity.dynamic_fields[attr_name].get('original'):
                        # For dynamic attributes, use the original expression
                        attr_expr = hy.read(entity.dynamic_fields[attr_name]['original'])
                    else:
                        # For static attributes, use the value
                        attr_expr = attr_value
                    
                    # Add attribute to node
                    node.attributes[attr_name] = attr_expr
                
                formatted_lines = type_plugin.format(node)
                lines.extend(formatted_lines)
                lines.append("")  # Add an empty line between entities
            
            # Write to file
            with open(file_path, "w") as f:
                f.write("\n".join(lines))
                
            self.logger.debug(f"Saved {len(entities)} {entity_type} entities to {file_path}")

    # Helper methods for working with entities

    def create_entity(
        self, 
        name: str, 
        entity_type: str,
        attributes: Optional[Dict[str, Any]] = None,
        dynamic_fields: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> TimeEntity:
        """Create a new time entity."""
        entity = self._time_entity_manager.create(
            name=name, 
            entity_type=entity_type,
            attributes=attributes or {},
            dynamic_fields=dynamic_fields or {}
        )
        
        # Add to items
        key = f"{entity_type}:{name}"
        self._items[key] = entity

        # Save immediately to persist the change
        self.save()

        return entity

    def get_entity(self, entity_type: str, name: str) -> Optional[TimeEntity]:
        """Get a specific entity by type and name."""
        key = f"{entity_type}:{name}"
        return self._items.get(key)

    def get_by_type(self, entity_type: str) -> List[TimeEntity]:
        """Get all entities of a specific type."""
        return [
            entity for key, entity in self._items.items()
            if entity.entity_type == entity_type
        ]

    def get_tasks(self) -> List[TimeEntity]:
        """Get all task entities."""
        return self.get_by_type("task")

    def get_habits(self) -> List[TimeEntity]:
        """Get all habit entities."""
        return self.get_by_type("habit")

    def get_events(self) -> List[TimeEntity]:
        """Get all event entities."""
        return self.get_by_type("event")

    def get_entity_types(self) -> List[str]:
        """Get all registered entity types."""
        return list(self.entity_types.keys())

    def get_task(self, name: str) -> Optional[TimeEntity]:
        """Get a specific task by name."""
        return self.get_entity("task", name)

    def get_habit(self, name: str) -> Optional[TimeEntity]:
        """Get a specific habit by name."""
        return self.get_entity("habit", name)

    def get_event(self, name: str) -> Optional[TimeEntity]:
        """Get a specific event by name."""
        return self.get_entity("event", name)

    def create_task(
        self,
        name: str,
        description: str = "",
        status: str = "pending",
        priority: str = "medium",
        due_date: Any = None,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> TimeEntity:
        """Create a new task."""
        task_attributes = attributes or {}
        task_attributes.update({
            "description": description,
            "status": status,
            "priority": priority,
            "due_date": due_date,
        })
        
        return self.create_entity(
            name=name,
            entity_type="task",
            attributes=task_attributes
        )

    def create_habit(
        self,
        name: str,
        description: str = "",
        frequency: str = "daily",
        start_date: Any = None,
        streak: int = 0,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> TimeEntity:
        """Create a new habit."""
        habit_attributes = attributes or {}
        habit_attributes.update({
            "description": description,
            "frequency": frequency,
            "start_date": start_date,
            "streak": streak,
        })
        
        return self.create_entity(
            name=name,
            entity_type="habit",
            attributes=habit_attributes
        )

    def create_event(
        self,
        name: str,
        title: str = "",
        description: str = "",
        start_time: Any = None,
        end_time: Any = None,
        location: str = "",
        attributes: Optional[Dict[str, Any]] = None,
    ) -> TimeEntity:
        """Create a new event."""
        event_attributes = attributes or {}
        event_attributes.update({
            "title": title,
            "description": description,
            "start_time": start_time,
            "end_time": end_time,
            "location": location,
        })
        
        return self.create_entity(
            name=name,
            entity_type="event",
            attributes=event_attributes
        )

    def get_entities_by_attribute(self, attr_name: str, attr_value: Any) -> List[TimeEntity]:
        """Get time entities with a specific attribute value."""
        return [
            entity for entity in self._items.values()
            if entity.has_attribute(attr_name) and entity.get_attribute(attr_name) == attr_value
        ]

    def remove_entity(self, name: str, entity_type: str) -> None:
        """Remove a time entity by name and type."""
        key = f"{entity_type}:{name}"
        if key in self._items:
            del self._items[key]
            # Save immediately to persist the change
            self.save()

    def update_entity_attribute(self, name: str, entity_type: str, attr_name: str, attr_value: Any):
        """Update a specific entity attribute value"""
        entity = self.get_entity(entity_type, name)
        if not entity:
            raise ValueError(f"Entity {entity_type}:{name} not found")

        # Update the attribute
        entity.set_attribute(attr_name, attr_value)
        
        # Save the updated entities
        self.save()

    def set_dynamic_attribute(self, name: str, entity_type: str, attr_name: str, attr_value: Any, original: str):
        """Set an attribute as dynamic with its original expression"""
        entity = self.get_entity(entity_type, name)
        if not entity:
            raise ValueError(f"Entity {entity_type}:{name} not found")
            
        # Set the dynamic field
        entity.set_dynamic_field(attr_name, attr_value, original)
        
        # Save the updated entities
        self.save()

    def rename_entity(self, old_name: str, new_name: str, entity_type: str):
        """Rename a time entity"""
        entity = self.get_entity(entity_type, old_name)
        if not entity:
            raise ValueError(f"Entity {entity_type}:{old_name} not found")

        # Create new entity with same properties
        new_entity = self.create_entity(
            name=new_name,
            entity_type=entity_type,
            attributes=entity.attributes,
            dynamic_fields=entity.dynamic_fields
        )

        # Remove old entity
        self.remove_entity(old_name, entity_type)

    # Advanced filtering methods

    def get_tasks_by_status(self, status: str) -> List[TimeEntity]:
        """Get all tasks with a specific status."""
        return [
            task for task in self.get_tasks()
            if task.get_attribute('status') == status
        ]

    def get_overdue_tasks(self) -> List[TimeEntity]:
        """Get all overdue tasks."""
        import datetime
        now = datetime.datetime.now()
        return [
            task for task in self.get_tasks()
            if task.get_attribute('due_date') and task.get_attribute('due_date') < now
            and task.get_attribute('status') != 'completed'
        ]

    def get_habits_by_frequency(self, frequency: str) -> List[TimeEntity]:
        """Get all habits with a specific frequency."""
        return [
            habit for habit in self.get_habits()
            if habit.get_attribute('frequency') == frequency
        ]

    def get_events_in_date_range(self, start_date: Any, end_date: Any) -> List[TimeEntity]:
        """Get all events within a date range."""
        return [
            event for event in self.get_events()
            if event.get_attribute('start_time') and start_date <= event.get_attribute('start_time') <= end_date
        ]
