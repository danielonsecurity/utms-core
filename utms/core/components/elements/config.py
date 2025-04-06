import os
from typing import Any, Dict, List, Optional, Union

from utms.core.components.base import SystemComponent
from utms.core.hy.ast import HyAST
from utms.core.loaders.base import LoaderContext
from utms.core.loaders.elements.config import ConfigLoader
from utms.core.managers.elements.config import ConfigManager
from utms.core.models.config import Config
from utms.core.plugins import plugin_registry
from utms.utils import hy_to_python


class ConfigComponent(SystemComponent):
    """Component managing UTMS configuration"""

    def __init__(self, config_dir: str, component_manager=None):
        super().__init__(config_dir, component_manager)
        self._ast_manager = HyAST()
        self._config_manager = ConfigManager()
        self._loader = ConfigLoader(self._config_manager)

    def load(self) -> None:
        """Load configuration from config.hy"""
        if self._loaded:
            return

        config_file = os.path.join(self._config_dir, "config.hy")
        if os.path.exists(config_file):
            try:
                nodes = self._ast_manager.parse_file(config_file)

                # Create context with variables
                context = LoaderContext(config_dir=self._config_dir)

                # Process nodes using loader
                self._items = self._loader.process(nodes, context)

                self._loaded = True

            except Exception as e:
                self.logger.error(f"Error loading config: {e}")
                raise

    def save(self) -> None:
        """Save configuration to config.hy"""
        config_file = os.path.join(self._config_dir, "config.hy")

        # Get the config plugin
        plugin = plugin_registry.get_node_plugin("custom-set-config")
        if not plugin:
            raise ValueError("Config plugin not found")

        # Create a node representing the entire config
        config_node = self._create_config_node()

        # Convert to Hy code and save
        content = "\n".join(plugin.format(config_node))
        with open(config_file, "w") as f:
            f.write(content + "\n")

    def _create_config_node(self) -> "HyNode":
        """
        Create a HyNode representing the entire configuration
        using the registered config plugin
        """
        # Get the config plugin
        plugin = plugin_registry.get_node_plugin("custom-set-config")
        if not plugin:
            raise ValueError("Config plugin not found")

        # Create a node with the custom-set-config type
        config_node = plugin.parse(
            ["custom-set-config"] + [[key, config.value] for key, config in self._items.items()]
        )

        return config_node

    def create_config(
        self, key: str, value: Any, is_dynamic: bool = False, original: Optional[str] = None
    ) -> Config:
        """Create a new config entry."""
        config = self._config_manager.create(
            key=key, value=value, is_dynamic=is_dynamic, original=original
        )

        # Save immediately to persist the change
        self.save()

        return config

    def get_config(self, key: str) -> Optional[Config]:
        """Get a config by key."""
        return self._config_manager.get(key)

    def get_configs_by_type(self, is_dynamic: bool) -> List[Config]:
        """Get configs filtered by dynamic status."""
        return self._config_manager.get_configs_by_type(is_dynamic)

    def remove_config(self, key: str) -> None:
        """Remove a config by key."""
        self._config_manager.remove(key)
        # Save immediately to persist the change
        self.save()

    def update_config(self, key: str, value: Any):
        """Update a specific config value"""
        config = self.get_config(key)
        if not config:
            raise ValueError(f"Config key {key} not found")

        # Update the value
        self._config_manager.create(
            key=key, value=value, is_dynamic=config.is_dynamic, original=config.original
        )

        # Save the updated configuration
        self.save()

    def rename_config_key(self, old_key: str, new_key: str):
        """Rename a config key"""
        config = self.get_config(old_key)
        if not config:
            raise ValueError(f"Config key {old_key} not found")

        # Create new config with same properties
        self._config_manager.create(
            key=new_key, value=config.value, is_dynamic=config.is_dynamic, original=config.original
        )

        # Remove old config
        self._config_manager.remove(old_key)

        # Save the updated configuration
        self.save()
