# utms/core/plugins/elements/dynamic_time_entity.py
from typing import Any, Dict, List, Optional, Type

import hy

from utms.core.hy.utils import format_value, is_dynamic_content
from utms.core.plugins import NodePlugin
from utms.core.models.elements.time_entity import TimeEntity
from utms.utms_types import HyNode
from utms.core.mixins.base import LoggerMixin

class DynamicTimeEntityPlugin(NodePlugin, LoggerMixin):
    """Base class for dynamically generated time entity plugins."""

    __discoverable__ = False

    
    def __init__(self, entity_type: str, default_attributes: Dict[str, Any]):
        self._entity_type = entity_type
        self._default_attributes = (default_attributes or {}).copy()
    
    @property
    def name(self) -> str:
        return f"{self._entity_type.capitalize()} Plugin"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def node_type(self) -> str:
        return f"def-{self._entity_type.lower()}"
    
    def initialize(self, system_context: Dict[str, Any]):
        pass

    def parse(self, expr) -> HyNode:
        """Parse entity definition."""
        if len(expr) < 2:
            return None

        entity_name = str(expr[1])
        
        self.logger.debug(f"Parsing {self._entity_type} entity: {entity_name}")
        
        # Create a dictionary to store attributes
        attributes = self._default_attributes.copy()
        dynamic_fields = {}
        
        # Process each attribute definition
        for i in range(2, len(expr)):
            # Check if it's a Hy expression
            if isinstance(expr[i], hy.models.Expression) and len(expr[i]) >= 2:
                attr_name = str(expr[i][0])
                attr_value = expr[i][1]
                
                self.logger.debug(f"  Attribute: {attr_name} = {attr_value}")
                
                # Store the attribute value
                attributes[attr_name] = attr_value
                
                # Check if the value is dynamic
                if is_dynamic_content(attr_value):
                    dynamic_fields[attr_name] = {
                        "original": hy.repr(attr_value).strip("'"),
                        "value": attr_value
                    }
            else:
                self.logger.debug(f"  Skipping: {expr[i]} - not a valid attribute expression")

        # Create the main entity node
        node = HyNode(
            type=self.node_type,
            value=entity_name,
            original=hy.repr(expr),
        )
        
        # Add entity_type and attributes as custom properties
        setattr(node, "entity_type", self._entity_type)
        setattr(node, "attributes", attributes)
        setattr(node, "dynamic_fields", dynamic_fields)
        
        self.logger.debug(f"Created node with {len(attributes)} attributes")
        return node

    def format(self, node: HyNode) -> List[str]:
        """Format entity definition back to Hy code."""
        attributes = getattr(node, "attributes", {})
        dynamic_fields = getattr(node, "dynamic_fields", {})
        
        if not attributes:
            return [f"({self.node_type} {node.value})"]

        lines = [f"({self.node_type} {node.value}"]
        
        # Format each attribute
        for field_name, value in attributes.items():
            # Format the value based on whether it's dynamic
            if field_name in dynamic_fields:
                value_str = dynamic_fields[field_name]["original"]
            else:
                value_str = format_value(value)
            
            lines.append(f"  ({field_name} {value_str})")
        
        lines.append(")")
        return lines


class DynamicTimeEntityPluginGenerator(LoggerMixin):
    """Generates time entity plugins dynamically based on entity type definitions."""
    
    def __init__(self):
        self.registered_plugins = {}
    


    def generate_plugin(self, entity_type: str, attributes: Dict[str, Any]) -> Type[NodePlugin]:
        """Generate a plugin class for a specific entity type."""
        # Create a new plugin class
        self.logger.debug("Generating plugin for entity type %s", entity_type)
        self.logger.debug("Attributes: %s", attributes)
        class DynamicPlugin(NodePlugin):
            def __init__(self):
                self._entity_type = entity_type
                self._default_attributes = attributes.copy()
                self.logger.debug("Initialized %s plugin with attributes %s", entity_type, self._default_attributes)

            @property
            def name(self) -> str:
                return f"{self._entity_type.capitalize()} Plugin"

            @property
            def version(self) -> str:
                return "0.1.0"

            @property
            def node_type(self) -> str:
                return f"def-{self._entity_type.lower()}"

            def initialize(self, system_context: Dict[str, Any]):
                pass

            def parse(self, expr) -> HyNode:
                """Parse entity definition."""
                if len(expr) < 2:
                    return None

                entity_name = str(expr[1])

                # Create a dictionary to store attributes
                attributes = self._default_attributes.copy()
                dynamic_fields = {}

                # Process each attribute definition
                for i in range(2, len(expr)):
                    # Check if it's a Hy expression
                    if isinstance(expr[i], hy.models.Expression) and len(expr[i]) >= 2:
                        attr_name = str(expr[i][0])
                        attr_value = expr[i][1]

                        # Store the attribute value
                        attributes[attr_name] = attr_value

                        # Check if the value is dynamic
                        if is_dynamic_content(attr_value):
                            dynamic_fields[attr_name] = {
                                "original": hy.repr(attr_value).strip("'"),
                                "value": attr_value
                            }

                # Create the main entity node
                node = HyNode(
                    type=self.node_type,
                    value=entity_name,
                    original=hy.repr(expr),
                )

                # Add entity_type and attributes as custom properties
                setattr(node, "entity_type", self._entity_type)
                setattr(node, "attributes", attributes)
                setattr(node, "dynamic_fields", dynamic_fields)

                return node

            def format(self, node: HyNode) -> List[str]:
                """Format entity definition back to Hy code."""
                attributes = getattr(node, "attributes", {})
                dynamic_fields = getattr(node, "dynamic_fields", {})

                if not attributes:
                    return [f"({self.node_type} {node.value})"]

                lines = [f"({self.node_type} {node.value}"]

                # Format each attribute
                for field_name, value in attributes.items():
                    # Format the value based on whether it's dynamic
                    if field_name in dynamic_fields:
                        value_str = dynamic_fields[field_name]["original"]
                    else:
                        value_str = format_value(value)

                    lines.append(f"  ({field_name} {value_str})")

                lines.append(")")
                return lines

        # Give the class a meaningful name
        DynamicPlugin.__name__ = f"{entity_type.capitalize()}Plugin"

        # Store the class for future reference
        self.registered_plugins[entity_type] = DynamicPlugin

        self.logger.debug("Created plugin class: %s", DynamicPlugin.__name__)
        return DynamicPlugin












# Create a singleton instance
plugin_generator = DynamicTimeEntityPluginGenerator()
