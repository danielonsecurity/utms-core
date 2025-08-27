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
from utms.utms_types import HyNode
from utms.utms_types.field.types import FieldType, TypedValue, infer_type


class VariableComponent(SystemComponent):
    """Component managing UTMS variables"""

    def __init__(self, config_dir: str, component_manager=None):
        super().__init__(config_dir, component_manager)
        self._ast_manager = HyAST()
        self._variable_manager = VariableManager()
        self._loader = VariableLoader(self._variable_manager)

    def _load_and_process_file(self, variables_file_path: str):
        """Parses a single variables.hy file and loads its contents."""
        if os.path.exists(variables_file_path):
            self.logger.debug(f"Loading variables from: {variables_file_path}")
            try:
                nodes = self._ast_manager.parse_file(variables_file_path)
                context = LoaderContext(config_dir=self._config_dir)
                self._items.update(self._loader.process(nodes, context))
            except Exception as e:
                self.logger.error(f"Error loading variables file {variables_file_path}: {e}")


    def load(self) -> None:
        """Load variables from variables.hy"""
        if self._loaded:
            return

        global_variables_file = os.path.join(self._config_dir, "global", "variables.hy")
        self._load_and_process_file(global_variables_file)

        config_component = self.get_component("config")
        if not config_component.is_loaded(): config_component.load()
        active_user_config = config_component.get_config("active-user")

        if active_user_config and (active_user := active_user_config.get_value()):
            user_variables_file = os.path.join(self._config_dir, "users", active_user, "variables.hy")
            self._load_and_process_file(user_variables_file)

        self._loaded = True

    def save(self) -> None:
        """Save variables to variables.hy"""
        config_component = self.get_component("config")
        if not config_component.is_loaded(): config_component.load()
        active_user_config = config_component.get_config("active-user")

        if not (active_user_config and (active_user := active_user_config.get_value())):
            self.logger.error("Cannot save variables: `active-user` is not defined.")
            return

        user_specific_dir = os.path.join(self._config_dir, "users", active_user)
        os.makedirs(user_specific_dir, exist_ok=True)
        
        variables_file = os.path.join(user_specific_dir, "variables.hy")

        plugin = plugin_registry.get_node_plugin("def-var")
        if not plugin:
            raise ValueError("Variable plugin not found")

        lines = []
        for key, variable_model in self._items.items():
            typed_value_instance: TypedValue = variable_model.value
            dummy_node_for_format = HyNode(
                type="def-var",
                value={"name": key, "typed_value_for_var_value": typed_value_instance},
                children=[],
                original=None,
            )

            lines.extend(plugin.format(dummy_node_for_format))
        with open(variables_file, "w") as f:
            f.write("\n\n".join(lines) + "\n")

    def create_variable(
        self,
        key: str,
        value: Any,
        is_dynamic: bool = False,
        original_expression: Optional[str] = None,
        field_type: Optional[Union[FieldType, str]] = None,
    ) -> Variable:
        """Create a new variable, now supporting TypedValue directly."""

        if isinstance(value, TypedValue):
            typed_value_for_manager = value
        else:
            if not field_type:
                field_type = infer_type(value)

            raw_value_for_typed_value = value
            if (
                is_dynamic
                and isinstance(value, str)
                and value.strip().startswith("(")
                and value.strip().endswith(")")
            ):
                try:
                    raw_value_for_typed_value = hy.read(value)
                except Exception as e:
                    self.logger.warning(
                        f"Failed to hy.read expression '{value}' for variable '{key}': {e}"
                    )

            typed_value_for_manager = TypedValue(
                value=raw_value_for_typed_value,
                field_type=field_type,
                is_dynamic=is_dynamic,
                original=original_expression,
            )

        variable = self._variable_manager.create(key=key, value=typed_value_for_manager)

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
        self.save()

    def update_variable(
        self,
        key: str,
        new_value: Any,
        is_dynamic: bool = False,
        original_expression: Optional[str] = None,
        field_type: Optional[Union[FieldType, str]] = None,
    ):
        """Update a variable's 'value' attribute."""
        variable = self.get_variable(key)
        if not variable:
            raise ValueError(f"Variable key {key} not found")

        if isinstance(new_value, TypedValue):
            updated_typed_value = new_value
        else:
            if not field_type:
                field_type = variable.value.field_type if variable.value else infer_type(new_value)

            raw_value_for_typed_value = new_value
            if (
                is_dynamic
                and isinstance(new_value, str)
                and new_value.strip().startswith("(")
                and new_value.strip().endswith(")")
            ):
                try:
                    raw_value_for_typed_value = hy.read(new_value)
                except Exception as e:
                    self.logger.warning(
                        f"Failed to hy.read expression '{new_value}' for update '{key}': {e}"
                    )

            elif not is_dynamic and isinstance(new_value, (hy.models.Expression, hy.models.Symbol)):
                resolved_val, _ = self._loader._dynamic_service.evaluate(
                    expression=new_value,
                    context=self.get_component("variables").items(),
                    component_type="variable_update",
                    component_label=key,
                    attribute="value",
                )
                raw_value_for_typed_value = (
                    resolved_val  
                )
                field_type = infer_type(raw_value_for_typed_value)  

            updated_typed_value = TypedValue(
                value=raw_value_for_typed_value,
                field_type=field_type,
                is_dynamic=is_dynamic,
                original=original_expression,
            )

        variable.value = updated_typed_value
        self._variable_manager.create(key=key, value=updated_typed_value)

        self.save()

    def rename_variable_key(self, old_key: str, new_key: str):
        """Rename a variable key."""
        variable = self.get_variable(old_key)
        if not variable:
            raise ValueError(f"Variable key {old_key} not found")

        self._variable_manager.create(
            key=new_key,
            value=variable.value,  
        )

        self._variable_manager.remove(old_key)

        self.save()

    def get_all_values(self) -> Dict[str, Any]:
        """
        Returns a dictionary of all variable names mapped to their resolved
        Python values, suitable for use as an evaluation context.
        """
        if not self._loaded:
            self.load()

        context_dict = {}
        for key, var_model in self.items():  
            if (
                var_model
                and hasattr(var_model, "value")
                and isinstance(var_model.value, TypedValue)
            ):
                context_dict[key] = var_model.value.value
                if "-" in key:
                    context_dict[key.replace("-", "_")] = var_model.value.value
            else:
                self.logger.warning(
                    f"Variable '{key}' has malformed data and will be skipped in context."
                )

        return context_dict
