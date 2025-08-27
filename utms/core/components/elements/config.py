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
from utms.utms_types import FieldType, HyNode, TypedValue, infer_type


class ConfigComponent(SystemComponent):
    """Component managing UTMS configuration"""

    def __init__(self, config_dir: str, component_manager=None):
        super().__init__(config_dir, component_manager)
        self._ast_manager = HyAST()
        self._config_manager = ConfigManager()
        self._loader = ConfigLoader(self._config_manager)

    def _load_and_process_file(self, config_file_path: str) -> None:
        """
        Parses a single config file and loads its contents into the manager.
        """
        if os.path.exists(config_file_path):
            self.logger.debug(f"Loading configuration from: {config_file_path}")
            try:
                nodes = self._ast_manager.parse_file(config_file_path)
                context = LoaderContext(config_dir=self._config_dir)
                self._loader.process(nodes, context)
            except Exception as e:
                self.logger.error(f"Error loading config file {config_file_path}: {e}")
        else:
            self.logger.debug(f"Configuration file not found, skipping: {config_file_path}")

    def load(self) -> None:
        """Load configuration from config.hy"""
        if self._loaded:
            return

        global_config_file = os.path.join(self._config_dir, "global", "config.hy")
        self._load_and_process_file(global_config_file)

        active_user_config = self.get_config("active-user")

        user_config_file = None
        if active_user_config:
            active_user = active_user_config.get_value()
            if active_user:
                self.logger.info(f"Found active user '{active_user}', loading their config.")
                user_config_file = os.path.join(self._config_dir, "users", active_user, "config.hy")
        
        self._load_and_process_file(user_config_file)
        self._loaded = True


    def save(self) -> None:
        active_user_config = self.get_config("active-user")
        
        if not active_user_config:
            self.logger.error("Cannot save config: `active-user` is not defined. Aborting save.")
            return

        active_user = active_user_config.get_value()
        user_config_dir = os.path.join(self._config_dir, "users", active_user)
        
        os.makedirs(user_config_dir, exist_ok=True)
        
        config_file = os.path.join(user_config_dir, "config.hy")
        self.logger.info(f"Saving configuration to user file: {config_file}")
        plugin = plugin_registry.get_node_plugin("custom-set-config")
        if not plugin:
            raise ValueError("Config plugin not found")

        config_node = self._create_config_node()

        content = "\n".join(plugin.format(config_node))
        with open(config_file, "w") as f:
            f.write(content + "\n")

    def _create_config_node(self) -> "HyNode":
        """
        Create a HyNode representing the entire configuration
        using the registered config plugin
        """
        plugin = plugin_registry.get_node_plugin("custom-set-config")
        config_entries = []
        for key, config in self._config_manager.get_all().items():
            if config.value.is_dynamic and config.value.original:
                value = hy.read(config.value.original)
            else:
                value = config.value.value

            if config.value.field_type != infer_type(config.value.value):
                config_entries.append([key, value, config.value.field_type.value])
            else:
                config_entries.append([key, value])

        config_node = plugin.parse(["custom-set-config"] + config_entries)
        return config_node

    def create_config(self, key: str, value: Any) -> Config:
        """Create a new config entry."""
        config = self._config_manager.create(key=key, value=value)

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
        self.save()

    def update_config(self, key: str, value: Any):
        """Update a config value"""
        config = self.get_config(key)
        if not config:
            raise ValueError(f"Config key {key} not found")

        if not isinstance(value, TypedValue):
            field_type = config.value.field_type
            is_dynamic = config.value.is_dynamic
            original = config.value.original

            typed_value = TypedValue(
                value=value, field_type=field_type, is_dynamic=is_dynamic, original=original
            )
        else:
            typed_value = value

        self._config_manager.create(key=key, value=typed_value)

        self.save()

    def set_dynamic_field(self, key: str, field_name: str, value: Any, original: str):
        """Set a field as dynamic with its original expression"""
        if field_name != "value":
            raise ValueError("Only 'value' field can be dynamic in Config objects")

        config = self.get_config(key)
        if not config:
            raise ValueError(f"Config key {key} not found")

        field_type = config.value.field_type

        typed_value = TypedValue(
            value=value, field_type=field_type, is_dynamic=True, original=original
        )

        self._config_manager.create(key=key, value=typed_value)

        self.save()

    def rename_config_key(self, old_key: str, new_key: str):
        """Rename a config key"""
        config = self.get_config(old_key)
        if not config:
            raise ValueError(f"Config key {old_key} not found")

        self._config_manager.create(
            key=new_key, value=config.value, dynamic_fields=config.dynamic_fields
        )

        self._config_manager.remove(old_key)

        self.save()
