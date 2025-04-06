from typing import Any, Dict, List

from utms.core.hy.resolvers.elements.variable import VariableResolver
from utms.core.loaders.base import ComponentLoader, LoaderContext
from utms.core.managers.elements.variable import VariableManager
from utms.core.models.variable import Variable
from utms.utms_types import HyNode, HyProperty
from utms.core.services.dynamic import DynamicResolutionService


class VariableLoader(ComponentLoader[Variable, VariableManager]):
    """Loader for Variable components."""

    def __init__(self, manager: VariableManager):
        super().__init__(manager)
        self._resolver = VariableResolver()
        self._dynamic_service = DynamicResolutionService(resolver=self._resolver)


    def parse_definitions(self, nodes: List[HyNode]) -> Dict[str, dict]:
        """Parse HyNodes into variable definitions.

        Args:
            nodes: List of HyNodes to parse

        Returns:
            Dictionary mapping variable names to their properties
        """
        variables = {}

        for node in nodes:
            if not self.validate_node(node, "def-var"):
                continue

            var_name = node.value
            if not node.children or len(node.children) == 0:
                self.logger.warning(f"Variable {var_name} has no value")
                continue

            value_node = node.children[0]
            variables[var_name] = {
                "value": value_node.value,
                "is_dynamic": value_node.is_dynamic,
                "original": value_node.original if value_node.is_dynamic else None,
            }

        return variables

    def create_object(self, label: str, properties: Dict[str, Any]) -> Variable:
        value = properties["value"]
        is_dynamic = properties.get("is_dynamic", False)
        original = properties.get("original")

        self.logger.debug(f"Creating variable {label} with value: {value}")

        # Use dynamic service for resolution if it's a dynamic expression
        if is_dynamic:
            resolved_value, dynamic_info = self._dynamic_service.evaluate(
                component_type='variable',
                component_label=label,
                attribute='value',
                expression=value,
                context=self.context.variables if self.context else None
            )
            self.logger.debug(f"Resolved dynamic value for {label}: {resolved_value}")

            # Store just the dynamic_info in resolver's vars
            self._resolver._resolved_vars[label] = dynamic_info
        else:
            resolved_value = value
            self.logger.debug(f"Using static value for {label}: {resolved_value}")

            # Store just the value for static vars
            self._resolver._resolved_vars[label] = resolved_value

        # Create Variable with HyProperty
        variable = Variable(
            name=label,
            property=HyProperty(
                value=resolved_value,
                original=original,
                is_dynamic=is_dynamic
            ),
        )

        return variable


    def process(self, nodes: List[HyNode], context: LoaderContext) -> Dict[str, Variable]:
        """Process nodes into Variables with resolution context.

        Override to handle variable-specific context
        """
        objects = super().process(nodes, context)
        self._manager._resolved_vars = {name: var.value for name, var in objects.items()}
        return objects
