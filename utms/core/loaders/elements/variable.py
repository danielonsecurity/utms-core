from typing import Any, Dict, List, Optional

import hy

from utms.core.hy.resolvers.elements.variable import VariableResolver
from utms.core.loaders.base import ComponentLoader, LoaderContext
from utms.core.managers.elements.variable import VariableManager
from utms.core.models import Variable
from utms.core.services.dynamic import DynamicResolutionService
from utms.utils import hy_to_python
from utms.utms_types import HyNode


class VariableLoader(ComponentLoader[Variable, VariableManager]):
    """Loader for Variable components."""

    def __init__(self, manager: VariableManager):
        super().__init__(manager)
        self._resolver = VariableResolver()
        self._dynamic_service = DynamicResolutionService(resolver=self._resolver)

    def parse_definitions(self, nodes: List[HyNode]) -> Dict[str, dict]:
        """Parse HyNodes into variable definitions."""
        variables = {}

        for node in nodes:
            if not self.validate_node(node, "def-var"):
                continue

            var_name = node.value
            if not node.children or len(node.children) == 0:
                self.logger.warning(f"Variable {var_name} has no value")
                continue

            # Initialize variable properties
            variable_props = {
                "key": var_name,
                "value": None,
                "dynamic_fields": {}
            }

            # Process each child node (currently just value, but could be extended)
            for child_node in node.children:
                field_name = getattr(child_node, "field_name", "value")
                
                # Store the field value
                variable_props[field_name] = child_node.value
                
                # If the field is dynamic, store its information
                if child_node.is_dynamic:
                    variable_props["dynamic_fields"][field_name] = {
                        "original": child_node.original,
                        "value": child_node.value
                    }

            variables[var_name] = variable_props

        return variables

    def create_object(self, key: str, properties: Dict[str, Any]) -> Variable:
        """Create a Variable from properties."""
        # Get the value and dynamic fields
        value = properties["value"]
        dynamic_fields = properties.get("dynamic_fields", {})
        
        self.logger.debug(f"Creating variable {key} with value: {value}")
        self.logger.debug(f"Dynamic fields: {dynamic_fields}")

        # Resolve dynamic expressions for each field
        for field_name, field_info in dynamic_fields.items():
            original_expr = field_info["original"]
            field_value = properties[field_name]
            
            # Only resolve if it's an expression
            if isinstance(field_value, (hy.models.Expression, hy.models.Symbol)):
                resolved_value, dynamic_info = self._dynamic_service.evaluate(
                    component_type="variable",
                    component_label=key,
                    attribute=field_name,
                    expression=field_value,
                    context=self.context.variables if self.context else None,
                )
                self.logger.debug(f"Resolved dynamic {field_name} for {key}: {resolved_value}")
                
                # Update the value in properties
                properties[field_name] = hy_to_python(resolved_value)
                
                # Update the dynamic field info
                dynamic_fields[field_name]["value"] = properties[field_name]
            else:
                self.logger.debug(f"Using static {field_name} for {key}: {field_value}")
                properties[field_name] = hy_to_python(field_value)

        # Create variable object
        return self._manager.create(
            key=key,
            value=properties["value"],
            dynamic_fields=dynamic_fields,
        )

    def process(self, nodes: List[HyNode], context: LoaderContext) -> Dict[str, Variable]:
        """Process variable nodes into Variable objects, updating context after each one."""
        # Initialize variables dictionary if not present
        if context and context.variables is None:
            context.variables = {}

        # First, parse definitions to get the order
        definitions = self.parse_definitions(nodes)

        # Process variables one by one to maintain dependency order
        objects = {}
        for label, properties in definitions.items():
            try:
                # Create a temporary list with just this node
                node_list = [n for n in nodes if self.validate_node(n, "def-var") and n.value == label]
                if not node_list:
                    continue

                # Process just this one node using the parent method
                temp_result = super().process(node_list, context)

                # Get the created object
                if label in temp_result:
                    obj = temp_result[label]
                    objects[label] = obj

                    # Update context with the newly resolved variable
                    if context and context.variables is not None:
                        context.variables[label] = obj.value
                        # Also add underscore version for Python compatibility
                        context.variables[label.replace("-", "_")] = obj.value

            except Exception as e:
                self.logger.error(f"Error processing variable {label}: {e}")
                raise

        # Load all objects into manager
        self._manager.load_objects(objects)

        return objects
