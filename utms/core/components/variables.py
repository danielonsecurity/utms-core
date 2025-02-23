import os
from typing import Dict, Optional, Any
from utms.utils import get_logger
from .base import SystemComponent
from utms.resolvers import HyAST
from ..variables import VariableManager
from utms.loaders.variable_loader import process_variables

logger = get_logger("core.components.variables")

class VariableComponent(SystemComponent):
    """Component managing variables"""
    
    def __init__(self, config_dir: str):
        super().__init__(config_dir)
        self._ast_manager = HyAST()
        self._variable_manager = VariableManager()

    def load(self) -> None:
        """Load variables from variables.hy"""
        if self._loaded:
            return

        variables_file = os.path.join(self._config_dir, "variables.hy")
        if os.path.exists(variables_file):
            try:
                breakpoint()
                nodes = self._ast_manager.parse_file(variables_file)
                self._variable_manager = process_variables(nodes)
                # Store variables in _items for dict-like access
                self._items = {
                    name: self._variable_manager.get_variable(name)
                    for name in self._variable_manager.resolved_vars.keys()
                }
                self._loaded = True
            except Exception as e:
                logger.error(f"Error loading variables: {e}")
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
