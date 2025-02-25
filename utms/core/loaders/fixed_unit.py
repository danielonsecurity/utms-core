from decimal import Decimal
from typing import Any, Dict, List

from utms.core.loaders.base import ComponentLoader
from utms.core.managers.fixed_unit import FixedUnitManager
from utms.core.models.fixed_unit import FixedUnit
from utms.resolvers.ast.node import HyNode
from utms.utms_types import HyProperty, UnitConfig


class FixedUnitLoader(ComponentLoader[FixedUnit, FixedUnitManager]):
    """Loader for FixedUnit components."""

    def parse_definitions(self, nodes: List[HyNode]) -> Dict[str, dict]:
        """Parse HyNodes into fixed unit definitions."""
        units = {}

        for node in nodes:
            if not self.validate_node(node, "def-fixed-unit"):
                continue

            unit_label = node.value
            unit_kwargs_dict = {}
            for prop in node.children:
                if prop.type == "property":
                    prop_name = prop.value
                    if prop.children:
                        prop_value = prop.children[0].value
                        unit_kwargs_dict[prop_name] = prop_value

            units[unit_label] = {"label": unit_label, "kwargs": unit_kwargs_dict}

        return units

    def create_object(self, label: str, properties: Dict[str, Any]) -> FixedUnit:
        """Create a FixedUnit from properties."""
        # Resolve properties
        resolved_name = properties["kwargs"].get("name")
        resolved_value = Decimal(properties["kwargs"].get("value"))
        resolved_groups = properties["kwargs"].get("groups", [])

        # Create FixedUnit
        fixed_unit = FixedUnit(
            label=label, name=resolved_name, value=resolved_value, groups=resolved_groups
        )

        return fixed_unit
