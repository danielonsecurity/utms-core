from typing import Any, Dict, List, Optional

from utms.core.managers.base import BaseManager
from utms.core.models import Config
from utms.utms_types import ConfigManagerProtocol, FieldType, TypedValue, infer_type


class ConfigManager(BaseManager[Config], ConfigManagerProtocol):
    """Manages configurations with their properties and relationships."""

    def create(
        self,
        key: str,
        value: Any,
    ) -> Config:
        """Create a new config entry."""
        if key in self._items:
            # If config exists, update it instead of raising an error
            self.remove(key)

        # Ensure value is a TypedValue
        if not isinstance(value, TypedValue):
            value = TypedValue(value, infer_type(value))

        # Create the config with the typed value
        config = Config(key=key, value=value)

        self.add(key, config)
        return config

    def get_configs_by_type(self, field_type: FieldType) -> List[Config]:
        """Get configs with values of a specific type."""
        return [config for config in self._items.values() if config.value.field_type == field_type]

    def get_configs_by_prefix(self, prefix: str) -> List[Config]:
        """Get configs with keys starting with a specific prefix."""
        return [config for config in self._items.values() if config.key.startswith(prefix)]

    def get_configs_by_dynamic(self, is_dynamic: bool) -> List[Config]:
        """Get configs filtered by whether their value is dynamic."""
        return [config for config in self._items.values() if config.value.is_dynamic == is_dynamic]

    def serialize(self) -> Dict[str, Dict[str, Any]]:
        """Convert configs to serializable format."""
        return {
            key: {
                "value": config.value.serialize(),
            }
            for key, config in self._items.items()
        }

    def deserialize(self, data: Dict[str, Dict[str, Any]]) -> None:
        """Load configs from serialized data."""
        self.clear()
        for key, config_data in data.items():
            value_data = config_data.get("value")

            # Create TypedValue from serialized data
            typed_value = TypedValue.deserialize(value_data)

            # Create config with typed value
            self.create(key=key, value=typed_value)
