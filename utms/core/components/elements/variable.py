import os
from typing import Any, Dict, List, Optional, Union

import hy

from utms.core.components.base import SystemComponent
from utms.core.hy.ast import HyAST
from utms.core.loaders.base import LoaderContext
from utms.core.loaders.elements.variable import VariableLoader
from utms.core.managers.elements.variable import VariableManager
from utms.core.models import Variable
from utms.core.plugins import plugin_registry
from utms.utils import hy_to_python


class VariableComponent(SystemComponent):
    """Component managing UTMS variables"""

    def __init__(self, config_dir: str, component_manager=None):
        super().__init__(config_dir, component_manager)
        self._ast_manager = HyAST()
        self._variable_manager = VariableManager()
        self._loader = VariableLoader(self._variable_manager)

    def load(self) -> None:
        """Load variables from variables.hy"""
        if self._loaded:
            return

        variables_file = os.path.join(self._config_dir, "variables.hy")
        if os.path.exists(variables_file):
            try:
                nodes = self._ast_manager.parse_file(variables_file)

                # Create context with variables
                context = LoaderContext(config_dir=self._config_dir)

                # Process nodes using loader
                self._items = self._loader.process(nodes, context)

                self._loaded = True

            except Exception as e:
                self.logger.error(f"Error loading variables: {e}")
                raise

    def save(self) -> None:
        """Save variables to variables.hy"""
        variables_file = os.path.join(self._config_dir, "variables.hy")
        
        # Get the variable plugin
        plugin = plugin_registry.get_node_plugin("def-var")
        if not plugin:
            raise ValueError("Variable plugin not found")
        
        # Create nodes for each variable
        lines = []
        for key, variable in self._items.items():
            # Create a node for this variable
            value_node = None
            
            # Check if the value field is dynamic
            if 'value' in variable.dynamic_fields and variable.dynamic_fields['value'].get('original'):
                # For dynamic variables, use the original expression
                value = hy.read(variable.dynamic_fields['value']['original'])
            else:
                # For static variables, use the value
                value = variable.value
                
            node = plugin.parse(["def-var", key, value])
            lines.extend(plugin.format(node))
        
        # Write to file with blank lines between variables
        with open(variables_file, "w") as f:
            f.write("\n\n".join(lines) + "\n")

    def create_variable(
        self, key: str, value: Any, dynamic_fields: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Variable:
        """Create a new variable."""
        variable = self._variable_manager.create(
            key=key, value=value, dynamic_fields=dynamic_fields or {}
        )

        # Save immediately to persist the change
        self.save()

        return variable

    def get_variable(self, key: str) -> Optional[Variable]:
        """Get a variable by key."""
        return self._variable_manager.get(key)

    def get_variables_by_dynamic_field(self, field_name: str, is_dynamic: bool) -> List[Variable]:
        """Get variables filtered by dynamic status of a specific field."""
        return self._variable_manager.get_variables_by_dynamic_field(field_name, is_dynamic)

    def remove_variable(self, key: str) -> None:
        """Remove a variable by key."""
        self._variable_manager.remove(key)
        # Save immediately to persist the change
        self.save()

    def update_variable(self, key: str, value: Any, field_name: str = "value"):
        """Update a specific variable field value"""
        variable = self.get_variable(key)
        if not variable:
            raise ValueError(f"Variable key {key} not found")

        # Get the current dynamic fields
        dynamic_fields = variable.dynamic_fields.copy()
        
        # If updating a dynamic field, preserve its dynamic status
        if field_name in dynamic_fields:
            dynamic_fields[field_name]["value"] = value
        
        # Create a new variable with updated field
        new_variable = self._variable_manager.create(
            key=key, 
            value=variable.value if field_name != "value" else value,
            dynamic_fields=dynamic_fields
        )
        
        # Update the specific field
        if field_name != "value":
            setattr(new_variable, field_name, value)
            
        self._items = self._variable_manager._items

        # Save the updated variables
        self.save()

    def set_dynamic_field(self, key: str, field_name: str, value: Any, original: str):
        """Set a field as dynamic with its original expression"""
        variable = self.get_variable(key)
        if not variable:
            raise ValueError(f"Variable key {key} not found")
            
        # Get the current dynamic fields
        dynamic_fields = variable.dynamic_fields.copy()
        
        # Update or add the dynamic field
        dynamic_fields[field_name] = {
            "original": original,
            "value": value
        }
        
        # Create a new variable with the updated dynamic field
        new_variable = self._variable_manager.create(
            key=key,
            value=value if field_name == "value" else variable.value,
            dynamic_fields=dynamic_fields
        )
        
        # Update the specific field
        if field_name != "value":
            setattr(new_variable, field_name, value)

        # Save the updated variables
        self.save()

    def rename_variable_key(self, old_key: str, new_key: str):
        """Rename a variable key"""
        variable = self.get_variable(old_key)
        if not variable:
            raise ValueError(f"Variable key {old_key} not found")

        # Create new variable with same properties
        self._variable_manager.create(
            key=new_key,
            value=variable.value,
            dynamic_fields=variable.dynamic_fields
        )

        # Remove old variable
        self._variable_manager.remove(old_key)

        # Save the updated variables
        self.save()
