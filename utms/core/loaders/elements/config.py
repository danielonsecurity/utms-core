from typing import Any, Dict, List, Optional

import hy

from utms.core.hy.resolvers.elements.config import ConfigResolver
from utms.core.loaders.base import ComponentLoader, LoaderContext
from utms.core.managers.elements.config import ConfigManager
from utms.core.models.config import Config
from utms.core.services.dynamic import DynamicResolutionService
from utms.utils import hy_to_python
from utms.utms_types import HyNode


class ConfigLoader(ComponentLoader[Config, ConfigManager]):
    """Loader for Config components."""

    def __init__(self, manager: ConfigManager):
        super().__init__(manager)
        self._resolver = ConfigResolver()
        self._dynamic_service = DynamicResolutionService()

    def parse_definitions(self, nodes: List[HyNode]) -> Dict[str, dict]:
        """Parse HyNodes into config definitions."""
        configs = {}

        for node in nodes:
            if not self.validate_node(node, "custom-set-config"):
                continue

            # Skip the first node (custom-set-config symbol)
            for setting in node.children:
                key = str(setting.value)
                value_node = setting.children[0]

                # Store both value and original if it's a dynamic expression
                config_entry = {
                    "key": key,
                    "value": value_node.value,
                    "is_dynamic": value_node.is_dynamic,
                    "original": value_node.original.strip("'") if value_node.is_dynamic else None,
                }
                configs[key] = config_entry

        return configs

    def create_object(self, key: str, properties: Dict[str, Any]) -> Config:
        """Create a Config from properties."""
        # Resolve the value using the config resolver
        value = properties["value"]
        is_dynamic = properties.get("is_dynamic", False)
        original = properties.get("original")
        self.logger.debug(f"Creating config {key} with value: {value}")

        # Resolve the value if it's an expression
        if isinstance(value, (hy.models.Expression, hy.models.Symbol)):
            resolved_value, dynamic_info = self._dynamic_service.evaluate(
                component_type="config",
                component_label=key,
                attribute="value",
                expression=value,
                context=self.context.variables if self.context else None,
            )
            self.logger.debug(f"Resolved dynamic value for {key}: {resolved_value}")

        else:
            resolved_value = value
            self.logger.debug(f"Using static value for {key}: {resolved_value}")

        # Convert to Python value
        resolved_value = hy_to_python(resolved_value)

        # Create config object
        return self._manager.create(
            key=key,
            value=resolved_value,
            is_dynamic=is_dynamic,
            original=original,
        )
