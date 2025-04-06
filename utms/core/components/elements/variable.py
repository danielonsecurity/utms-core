import os
from typing import Any, Dict, Optional

from utms.core.hy.ast import HyAST
from utms.core.loaders.base import LoaderContext
from utms.core.loaders.elements.variable import VariableLoader
from utms.core.managers.elements.variable import VariableManager

from utms.core.components.base import SystemComponent


class VariableComponent(SystemComponent):
    """Component managing variables"""

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

                context = LoaderContext(config_dir=self._config_dir, variables=self._items)

                self._items = self._loader.process(nodes, context)

                self._variable_manager._items = self._items
                self._variable_manager._resolved_vars = {
                    name: var.value for name, var in self._items.items()
                }
                self._loaded = True

            except Exception as e:
                self.logger.error(f"Error loading variables: {e}")
                raise

    def save(self) -> None:
        """Save variables to variables.hy"""
        variables_file = os.path.join(self._config_dir, "variables.hy")
        self._variable_manager.save(variables_file)

    def get_value(self, name: str) -> Any:
        """Get resolved value of a variable"""
        return self._variable_manager.get_value(name)

    def get_variable(self, name: str):
        """Get variable object"""
        return self._variable_manager.get_variable(name)

    @property
    def resolved_vars(self) -> Dict[str, Any]:
        """Get all resolved variables"""
        return self._variable_manager.resolved_vars
