import os
from pathlib import Path
from typing import Any, Dict, Optional

from utms.core.components.base import SystemComponent
from utms.core.hy import evaluate_hy_file
from utms.core.hy.resolvers import ConfigResolver
from utms.utils import hy_to_python, python_to_hy

class ConfigComponent(SystemComponent):
    """Component managing UTMS configuration"""
    
    def __init__(self, config_dir: str, component_manager=None):
        super().__init__(config_dir, component_manager)
        self._resolver = ConfigResolver()

    def load(self) -> None:
        """Load configuration from config.hy"""
        if self._loaded:
            return

        config_file = os.path.join(self._config_dir, "config.hy")
        self.logger.debug(f"Loading config from: {config_file}")
        
        if os.path.exists(config_file):
            try:
                expressions = evaluate_hy_file(config_file)
                if expressions:
                    self.logger.debug(f"Resolving config expressions: {expressions[0]}")
                    config = self._resolver.resolve_config_property(expressions[0])
                    self.logger.debug(f"Resolved config: {config}")
                    self._items = config
                    self.logger.debug("Configuration loaded successfully")
            except Exception as e:
                self.logger.error(f"Error loading config: {e}")
                raise
        else:
            self.logger.warning(f"Config file not found: {config_file}")
            
        self._loaded = True

    def save(self) -> None:
        """Save configuration to config.hy"""
        config_file = os.path.join(self._config_dir, "config.hy")
        
        settings = []
        for key, value in self._items.items():
            formatted_value = python_to_hy(value)
            settings.append(f"  '({key} {formatted_value})")

        content = [
            ";; This file is managed by UTMS - do not edit manually",
            "(custom-set-config",
            *sorted(settings),
            ")",
        ]

        with open(config_file, "w") as f:
            f.write("\n".join(content))

