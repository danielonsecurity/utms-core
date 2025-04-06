from typing import Any, Dict, List, Optional, Union

from utms.utms_types import ConfigManagerProtocol

from utms.core.models.config import Config
from utms.core.managers.base import BaseManager


class ConfigManager(BaseManager[Config], ConfigManagerProtocol):
    """Manages configurations with their properties and relationships."""

    def create(
        self,
        key: str,
        value: Any,
        is_dynamic: bool = False,
        original: Optional[str] = None,
    ) -> Config:
        """Create a new config entry."""
        if key in self._items:
            raise ValueError(f"Config with key '{key}' already exists")

        config = Config(
            key=key,
            value=value,
            is_dynamic=is_dynamic,
            original=original,
        )

        self.add(key, config)
        return config

    def get_configs_by_type(self, is_dynamic: bool) -> List[Config]:
        """Get configs filtered by dynamic status."""
        return [
            config for config in self._items.values() 
            if config.is_dynamic == is_dynamic
        ]

    def get_configs_by_prefix(self, prefix: str) -> List[Config]:
        """Get configs with keys starting with a specific prefix."""
        return [
            config for config in self._items.values()
            if config.key.startswith(prefix)
        ]

    def serialize(self) -> Dict[str, Dict[str, Any]]:
        """Convert configs to serializable format."""
        return {
            key: {
                "value": str(config.value),
                "is_dynamic": config.is_dynamic,
                "original": config.original,
            }
            for key, config in self._items.items()
        }

    def deserialize(self, data: Dict[str, Dict[str, Any]]) -> None:
        """Load configs from serialized data."""
        self.clear()
        for key, config_data in data.items():
            self.create(
                key=key,
                value=config_data["value"],
                is_dynamic=config_data.get("is_dynamic", False),
                original=config_data.get("original"),
            )
