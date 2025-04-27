from typing import Any, Dict, List, Optional

import hy

from utms.core.hy.resolvers.elements.config import ConfigResolver
from utms.core.loaders.base import ComponentLoader, LoaderContext
from utms.core.managers.elements.config import ConfigManager
from utms.core.models import Config
from utms.core.services.dynamic import DynamicResolutionService
from utms.utils import hy_to_python
from utms.utms_types import HyNode, TypedValue, FieldType, infer_type


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
                        original=value_node.original
                    )
                
                # Initialize config properties
                config_props = {
                    "key": key,
                    "value": typed_value
                }
                
                configs[key] = config_props

        return configs

    def create_object(self, key: str, properties: Dict[str, Any]) -> Config:
        """Create a Config from properties."""
        # Get the typed value
        typed_value = properties["value"]
        
        # Ensure we have a TypedValue
        if not isinstance(typed_value, TypedValue):
            typed_value = TypedValue(
                value=typed_value,
                field_type=infer_type(typed_value),
                is_dynamic=False
            )
        
        self.logger.debug(f"Creating config {key} with value: {typed_value.value}")
        self.logger.debug(f"Type: {typed_value.field_type}, Dynamic: {typed_value.is_dynamic}")

        # Resolve dynamic expressions
        if typed_value.is_dynamic:
            value = typed_value.value
            # Only resolve if it's an expression
            if isinstance(value, (hy.models.Expression, hy.models.Symbol)):
                resolved_value, dynamic_info = self._dynamic_service.evaluate(
                    component_type="config",
                    component_label=key,
                    attribute="value",
                    expression=value,
                    context=self.context.variables if self.context else None,
                )
                self.logger.debug(f"Resolved dynamic value for {key}: {resolved_value}")
                
                # Create a new TypedValue with the resolved value but keep type info
                python_value = hy_to_python(resolved_value)
                typed_value = TypedValue(
                    value=python_value,
                    field_type=typed_value.field_type,
                    is_dynamic=True,
                    original=typed_value.original
                )
            else:
                self.logger.debug(f"Using static value for {key}: {value}")
                # Convert to Python value but keep type info
                python_value = hy_to_python(value)
                typed_value.value = python_value

        # Create config object
        return self._manager.create(key=key, value=typed_value)
