import os
from argparse import Namespace
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional

import hy

from utms.core.components.base import SystemComponent
from utms.core.hy.ast import HyAST
from utms.core.loaders.base import LoaderContext
from utms.core.loaders.elements.fixed_unit import FixedUnitLoader
from utms.core.managers.elements.fixed_unit import FixedUnitManager
from utms.core.models.fixed_unit import FixedUnit
from utms.core.plugins import plugin_registry
from utms.utms_types import HyNode


class FixedUnitComponent(SystemComponent):
    """Component managing fixed units."""

    def __init__(self, config_dir: str, component_manager=None):
        super().__init__(config_dir, component_manager)
        self._ast_manager = HyAST()
        self._fixed_unit_manager = FixedUnitManager()
        self._loader = FixedUnitLoader(self._fixed_unit_manager)

    def load(self) -> None:
        """Load fixed units from fixed_units.hy"""
        if self._loaded:
            return

        fixed_units_file = Path(self._config_dir) / "fixed_units.hy"
        if fixed_units_file.exists():
            try:
                # Parse file into nodes
                nodes = self._ast_manager.parse_file(str(fixed_units_file))

                # Create context
                context = LoaderContext(
                    config_dir=self._config_dir, variables=self._items  # Pass existing items if any
                )

                # Process nodes using loader
                self._items = self._loader.process(nodes, context)

                # Update manager's items
                self._fixed_unit_manager._items = self._items

                self._loaded = True

            except Exception as e:
                self.logger.error(f"Error loading fixed units: {e}")
                raise

    def save(self) -> None:
        """Save fixed units to fixed_units.hy"""
        fixed_units_file = Path(self._config_dir) / "fixed_units.hy"

        # Get the fixed unit plugin
        plugin = plugin_registry.get_node_plugin("def-fixed-unit")
        if not plugin:
            raise ValueError("Fixed Unit plugin not found")

        # Create nodes from current items
        nodes = self._data_to_nodes(self._items)

        # Convert to Hy code and save
        content = self._ast_manager.to_hy(nodes)
        fixed_units_file.write_text(content)

    def _data_to_nodes(self, data: Dict[str, FixedUnit]) -> List[HyNode]:
        """Convert dictionary of FixedUnit to nodes"""
        plugin = plugin_registry.get_node_plugin("def-fixed-unit")
        if not plugin:
            raise ValueError("Fixed Unit plugin not found")

        nodes = []
        for label, unit in data.items():
            # Create expression parts
            expr_parts = [hy.models.Symbol("def-fixed-unit"), hy.models.Symbol(label)]

            # Add properties
            properties = [
                hy.models.Expression([hy.models.Symbol("name"), hy.models.String(unit.name)]),
                hy.models.Expression(
                    [hy.models.Symbol("value"), hy.models.Float(float(unit.value))]
                ),
            ]

            # Add groups if they exist
            if unit.groups:
                properties.append(
                    hy.models.Expression(
                        [
                            hy.models.Symbol("groups"),
                            hy.models.List([hy.models.String(group) for group in unit.groups]),
                        ]
                    )
                )

            # Add properties to expression
            expr_parts.extend(properties)

            # Create the full expression
            expr = hy.models.Expression(expr_parts)

            # Use the plugin to parse the expression
            nodes.append(plugin.parse(expr))

        return nodes

    def get_unit(self, label: str) -> Any:
        """Get a fixed unit by label"""
        return self._fixed_unit_manager.get(label)

    def get_all_units(self) -> Dict[str, Any]:
        """Get all fixed units"""
        return self._fixed_unit_manager.get_all()

    def get_units_by_group(self, group):
        """Get all fixed units"""
        return self._fixed_unit_manager.get_units_by_group(group)

    def get_units_by_groups(self, groups, match_all: bool = False):
        """Get all fixed units"""
        return self._fixed_unit_manager.get_units_by_groups(groups, match_all)

    def add_unit(self, unit: FixedUnit) -> None:
        """Add a fixed unit."""
        self._fixed_unit_manager.add(unit.label, unit)

    def remove_unit(self, label: str) -> None:
        """Remove a fixed unit by label."""
        self._fixed_unit_manager.remove(label)

    def create_unit(
        self, label: str, name: str, value: Decimal, groups: Optional[List[str]] = None
    ) -> FixedUnit:
        """Create a new fixed unit."""
        return self._fixed_unit_manager.create(label=label, name=name, value=value, groups=groups)

    def convert(self, args: Namespace):
        return self._fixed_unit_manager.convert_units(args)

    def print(self, args: Namespace):
        return self._fixed_unit_manager.print(args)
