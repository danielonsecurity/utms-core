from typing import Any, Dict, List, Optional, Union

from utms.core.managers.base import BaseManager
from utms.core.models import Variable
from utms.utms_types import VariableManagerProtocol


class VariableManager(BaseManager[Variable], VariableManagerProtocol):
    """Manages variables with their properties and relationships."""

    def create(
        self,
        key: str,
        value: Any,
        dynamic_fields: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> Variable:
        """Create a new variable entry."""
        if key in self._items:
            # If variable exists, update it instead of raising an error
            self.remove(key)
            
        # Create the variable with dynamic fields
        variable = Variable(
            key=key,
            value=value,
            dynamic_fields=dynamic_fields or {},
        )

        self.add(key, variable)
        return variable

    def get_variables_by_dynamic_field(self, field_name: str, is_dynamic: bool) -> List[Variable]:
        """Get variables filtered by dynamic status of a specific field."""
        return [
            variable for variable in self._items.values() 
            if variable.is_field_dynamic(field_name) == is_dynamic
        ]

    def get_variables_by_prefix(self, prefix: str) -> List[Variable]:
        """Get variables with keys starting with a specific prefix."""
        return [variable for variable in self._items.values() if variable.key.startswith(prefix)]

    def serialize(self) -> Dict[str, Dict[str, Any]]:
        """Convert variables to serializable format."""
        return {
            key: {
                "value": str(variable.value),
                "dynamic_fields": variable.dynamic_fields,
            }
            for key, variable in self._items.items()
        }

    def deserialize(self, data: Dict[str, Dict[str, Any]]) -> None:
        """Load variables from serialized data."""
        self.clear()
        for key, variable_data in data.items():
            self.create(
                key=key,
                value=variable_data["value"],
                dynamic_fields=variable_data.get("dynamic_fields", {}),
            )
