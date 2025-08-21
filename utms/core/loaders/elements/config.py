from typing import Any, Dict, List, Optional

import hy

from utms.core.hy.resolvers.elements.config import ConfigResolver
from utms.core.loaders.base import ComponentLoader, LoaderContext
from utms.core.managers.elements.config import ConfigManager
from utms.core.models import Config
from utms.core.services.dynamic import DynamicResolutionService
from utms.core.hy.converter import converter
from utms.utms_types import FieldType, HyNode, TypedValue, infer_type


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

            for setting in node.children:
                key = str(setting.value)
                value_node = setting.children[0]

                # Get the typed value from the node
                typed_value = None
                if isinstance(value_node.value, TypedValue):
                    typed_value = value_node.value
                else:
                    # Create a TypedValue if not already present
                    field_type = infer_type(value_node.value)
                    typed_value = TypedValue(
                        value=value_node.value,
                        field_type=field_type,
                        is_dynamic=value_node.is_dynamic,
                        original=value_node.original,
                    )

                # Initialize config properties
                config_props = {"key": key, "value": typed_value}

                configs[key] = config_props

        return configs

    def create_object(self, key: str, properties: Dict[str, Any]) -> Config:
        """Create a Config from properties."""
        # Get the typed value
        typed_value = properties["value"]

        # Ensure we have a TypedValue
        if not isinstance(typed_value, TypedValue):
            typed_value = TypedValue(
                value=typed_value, field_type=infer_type(typed_value), is_dynamic=False
            )

        self.logger.debug(f"Creating config {key} with value: {typed_value.value}")
        self.logger.debug(f"Type: {typed_value.field_type}, Dynamic: {typed_value.is_dynamic}")

        if typed_value.is_dynamic:
            value = typed_value.value
            if isinstance(value, (hy.models.Expression, hy.models.Symbol)):
                resolved_value, dynamic_info = self._dynamic_service.evaluate(
                    component_type="config",
                    component_label=key,
                    attribute="value",
                    expression=value,
                    context=self.context.variables if self.context else None,
                )
                self.logger.debug(f"Resolved dynamic value for {key}: {resolved_value}")

                python_value = converter.model_to_py(resolved_value, raw=True)
                typed_value = TypedValue(
                    value=python_value,
                    field_type=typed_value.field_type,
                    is_dynamic=True,
                    original=typed_value.original,
                )
            else:
                self.logger.debug(f"Using static value for {key}: {value}")
                python_value = converter.model_to_py(value, raw=True)
                typed_value.value = python_value

        return self._manager.create(key=key, value=typed_value)
