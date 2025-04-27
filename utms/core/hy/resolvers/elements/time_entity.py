from datetime import datetime
import time
from typing import Any, Dict, List

import hy

from utms.core.hy.resolvers.base import HyResolver
from utms.core.hy.utils import format_value, is_dynamic_content
from utms.utils import get_ntp_date, get_timezone_from_seconds
from utms.utms_types import Context, HyExpression, LocalsDict, ResolvedValue, is_expression, DynamicExpressionInfo, HyNode


class TimeEntityResolver(HyResolver):
    """Resolver for time entity expressions in Hy code."""

    def __init__(self) -> None:
        super().__init__()
        self._resolved_entities = {}
        self._resolved_attributes = {}

    def resolve(
        self, 
        expression: HyExpression, 
        context: Context = None, 
        local_names: LocalsDict = None
    ) -> tuple[ResolvedValue, DynamicExpressionInfo]:
        """Resolve a time entity expression for any attribute."""
        # First, get the result from the parent class
        resolved_value, dynamic_info = super().resolve(expression, context, local_names)
        
        # If this is a named entity attribute (from context), store its resolved value
        if context and 'current_label' in context and 'current_field' in context:
            entity_key = context['current_label']
            attr_name = context['current_field']
            
            # Create a compound key for the attribute
            attr_key = f"{entity_key}.{attr_name}"
            
            if isinstance(resolved_value, DynamicExpressionInfo):
                self._resolved_attributes[attr_key] = resolved_value.latest_value
            else:
                self._resolved_attributes[attr_key] = resolved_value

            self.logger.debug(f"Stored resolved value for {attr_key}: {self._resolved_attributes[attr_key]}")

        return resolved_value, dynamic_info

    def get_locals_dict(self, context: Context, local_names: LocalsDict = None) -> LocalsDict:
        """Provide time entity-specific context for Hy evaluation"""
        locals_dict = super().get_locals_dict(context, local_names)

        # Add time-related utilities
        locals_dict.update({
            "datetime": datetime,
            "time": time,
            "get_ntp_date": get_ntp_date,
            "get_timezone": get_timezone_from_seconds,
            "now": lambda: int(time.time()),
            **self._resolved_attributes,
        })
        
        # Add all resolved attributes to the locals dict
        for name, value in self._resolved_attributes.items():
            if isinstance(value, DynamicExpressionInfo):
                actual_value = value.latest_value
            else:
                actual_value = value
                
            # Add both with hyphens and underscores for compatibility
            locals_dict[name] = actual_value
            locals_dict[name.replace("-", "_")] = actual_value
            
            # Also add the entity-specific versions if this is a compound key
            if "." in name:
                entity_key, attr_name = name.split(".", 1)
                if entity_key not in locals_dict:
                    locals_dict[entity_key] = {}
                if not isinstance(locals_dict[entity_key], dict):
                    locals_dict[entity_key] = {"name": locals_dict[entity_key]}
                locals_dict[entity_key][attr_name] = actual_value
                
                # Underscore version
                entity_key_us = entity_key.replace("-", "_")
                attr_name_us = attr_name.replace("-", "_")
                if entity_key_us not in locals_dict:
                    locals_dict[entity_key_us] = {}
                if not isinstance(locals_dict[entity_key_us], dict):
                    locals_dict[entity_key_us] = {"name": locals_dict[entity_key_us]}
                locals_dict[entity_key_us][attr_name_us] = actual_value
        
        self.logger.debug("Locals dict contains: %s", locals_dict.keys())
        return locals_dict

    def parse_node(self, expr) -> HyNode:
        """Parse a time entity definition expression."""
        if not isinstance(expr, list) or len(expr) < 3:
            return None

        # Check if this is a time entity definition
        if not self._is_time_entity_def(expr):
            return None

        entity_name = str(expr[1])
        entity_type = str(expr[2]) if len(expr) > 2 else "generic"

        # Parse attributes
        attribute_nodes = []
        for i in range(3, len(expr)):
            if isinstance(expr[i], list) and len(expr[i]) >= 2:
                attr_name = str(expr[i][0])
                attr_value = expr[i][1]

                # Check if the value is dynamic
                is_dynamic = is_dynamic_content(attr_value)

                # Create attribute node
                attr_node = HyNode(
                    type="attribute",
                    value=attr_value,
                    original=hy.repr(attr_value).strip("'") if is_dynamic else None,
                    is_dynamic=is_dynamic,
                    field_name=attr_name
                )
                attribute_nodes.append(attr_node)

        # Create the main time entity node
        node = HyNode(
            type="def-time-entity",
            value=entity_name,
            original=hy.repr(expr),
        )

        # Add entity_type as metadata
        node.metadata = {"entity_type": entity_type}
        node.children = attribute_nodes

        return node


    def format_node(self, node: HyNode) -> List[str]:
        """Format a time entity node back to Hy code."""
        if node.type != "def-time-entity":
            return []

        entity_type = getattr(node, "metadata", {}).get("entity_type", "generic")
        lines = [f"(def-time-entity {node.value} {entity_type}"]

        # Format attributes
        for child in node.children:
            if hasattr(child, "is_dynamic") and child.is_dynamic and hasattr(child, "original") and child.original:
                value_str = child.original
            else:
                value_str = format_value(child.value)

            lines.append(f"  ({child.field_name} {value_str})")

        lines.append(")")
        return lines
