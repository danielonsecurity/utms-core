from typing import Any, Dict, List

from utms.core.loaders.base import ComponentLoader, LoaderContext
from utms.core.managers.variable import VariableManager
from utms.core.models.variable import Variable
from utms.resolvers import VariableResolver
from utms.resolvers.ast.node import HyNode
from utms.utms_types import HyProperty


class VariableLoader(ComponentLoader[Variable, VariableManager]):
    """Loader for Variable components."""

    def __init__(self, manager: VariableManager):
        super().__init__(manager)
        self._resolver = VariableResolver()

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
                "original": value_node.original if value_node.is_dynamic else None,
            }

        return variables

    def create_object(self, label: str, properties: Dict[str, Any]) -> Variable:
        """Create a Variable from properties.

        Args:
            label: Variable name
            properties: Variable properties including value and original

        Returns:
            Created Variable object
        """
        # Resolve the value
        resolved_value = self._resolver.resolve(properties["value"])

        # Create Variable with HyProperty
        variable = Variable(
            name=label,
            property=HyProperty(value=resolved_value, original=properties.get("original")),
        )

        # Update resolver's state
        self._resolver._resolved_vars[label] = resolved_value

        return variable

    def process(self, nodes: List[HyNode], context: LoaderContext) -> Dict[str, Variable]:
        """Process nodes into Variables with resolution context.

        Override to handle variable-specific context
        """
        objects = super().process(nodes, context)
        self._manager._resolved_vars = {name: var.value for name, var in objects.items()}
        return objects
