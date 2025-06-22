from typing import Any, Dict, List, Optional, Union

from utms.core.managers.base import BaseManager
from utms.core.models import Variable
from utms.utms_types import VariableManagerProtocol
from utms.utms_types.field.types import TypedValue


class VariableManager(BaseManager[Variable]):
    """Manages variables with their properties and relationships."""

    def create(
        self,
        key: str,
        value: TypedValue,
    ) -> Variable:
        """Create a new variable entry."""
        if key in self._items:
            self.remove(key)

        variable = Variable(
            key=key,
            value=value,
        )

        self.add(key, variable)
        return variable

    def get_variables_by_dynamic_field(self, field_name: str, is_dynamic: bool) -> List[Variable]:
        """Get variables filtered by dynamic status of a specific field (e.g., 'value')."""
        return [
            variable
            for variable in self._items.values()
            if variable.is_field_dynamic(field_name) == is_dynamic
        ]

    def get_variables_by_prefix(self, prefix: str) -> List[Variable]:
        """Get variables with keys starting with a specific prefix."""
        return [variable for variable in self._items.values() if variable.key.startswith(prefix)]

    def serialize(self) -> Dict[str, Dict[str, Any]]:
        """Convert variables to serializable format, using TypedValue.serialize()."""
        return {
            key: {
                "value": variable.value.serialize(),  # Use TypedValue's serialize for API/JSON
            }
            for key, variable in self._items.items()
        }

    def deserialize(self, data: Dict[str, Dict[str, Any]]) -> None:
        """Load variables from serialized data, using TypedValue.deserialize()."""
        self.clear()
        for key, variable_data in data.items():
            typed_value_from_data = TypedValue.deserialize(variable_data["value"])
            self.create(
                key=key,
                value=typed_value_from_data,
            )
