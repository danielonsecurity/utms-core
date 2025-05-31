import os
from typing import Any, Dict, List, Optional, Union

import hy

from utms.core.components.base import SystemComponent
from utms.core.hy.ast import HyAST
from utms.core.loaders.base import LoaderContext
from utms.core.loaders.elements.config import ConfigLoader
from utms.core.managers.elements.config import ConfigManager
from utms.core.models import Config
from utms.core.plugins import plugin_registry
from utms.utils import hy_to_python
from utms.utms_types import HyNode, TypedValue, FieldType, infer_type



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
        config_entries = []
        for key, config in self._config_manager.get_all().items():
            # Check if the value is dynamic
            if config.value.is_dynamic and config.value.original:
                # For dynamic configs, use the original expression
                value = hy.read(config.value.original)
            else:
                # For static configs, use the value
                value = config.value.value

            # Add type information as third element if it's not the default type
            if config.value.field_type != infer_type(config.value.value):
                config_entries.append([key, value, config.value.field_type.value])
            else:
                config_entries.append([key, value])

        config_node = plugin.parse(["custom-set-config"] + config_entries)
        return config_node

    def create_config(
        self, key: str, value: Any
    ) -> Config:
        """Create a new config entry."""
        # Let the manager handle TypedValue conversion
        config = self._config_manager.create(key=key, value=value)

        # Save immediately to persist the change
        self.save()

        return config


    def get_config(self, key: str) -> Optional[Config]:
        """Get a config by key."""
        return self._config_manager.get(key)

    def get_configs_by_dynamic_field(self, field_name: str, is_dynamic: bool) -> List[Config]:
        """Get configs filtered by dynamic status of a specific field."""
        return self._config_manager.get_configs_by_dynamic_field(field_name, is_dynamic)

    def remove_config(self, key: str) -> None:
        """Remove a config by key."""
        self._config_manager.remove(key)
        # Save immediately to persist the change
        self.save()

    def update_config(self, key: str, value: Any):
        """Update a config value"""
        config = self.get_config(key)
        if not config:
            raise ValueError(f"Config key {key} not found")

        # Create a new TypedValue if needed, preserving type
        if not isinstance(value, TypedValue):
            field_type = config.value.field_type
            is_dynamic = config.value.is_dynamic
            original = config.value.original

            typed_value = TypedValue(
                value=value,
                field_type=field_type,
                is_dynamic=is_dynamic,
                original=original
            )
        else:
            typed_value = value

        # Create a new config with the updated value
        self._config_manager.create(key=key, value=typed_value)

        # Save the updated configuration
        self.save()


    def set_dynamic_field(self, key: str, field_name: str, value: Any, original: str):
        """Set a field as dynamic with its original expression"""
        if field_name != "value":
            raise ValueError("Only 'value' field can be dynamic in Config objects")

        config = self.get_config(key)
        if not config:
            raise ValueError(f"Config key {key} not found")

        # Determine field type from existing config
        field_type = config.value.field_type

        # Create a TypedValue with dynamic properties
        typed_value = TypedValue(
            value=value,
            field_type=field_type,
            is_dynamic=True,
            original=original
        )

        # Create a new config with the dynamic value
        self._config_manager.create(key=key, value=typed_value)

        # Save the updated configuration
        self.save()

    def rename_config_key(self, old_key: str, new_key: str):
        """Rename a config key"""
        config = self.get_config(old_key)
        if not config:
            raise ValueError(f"Config key {old_key} not found")

        # Create new config with same properties
        self._config_manager.create(
            key=new_key,
            value=config.value,
            dynamic_fields=config.dynamic_fields
        )

        # Remove old config
        self._config_manager.remove(old_key)

        # Save the updated configuration
        self.save()
