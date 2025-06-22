import os
from argparse import Namespace
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional

import hy

from utms.core.components.base import SystemComponent
from utms.core.hy.ast import HyAST
from utms.core.loaders.base import LoaderContext
from utms.core.loaders.elements.unit import UnitLoader
from utms.core.managers.elements.unit import UnitManager
from utms.core.models import Unit
from utms.core.plugins import plugin_registry
from utms.utms_types import HyNode


class UnitComponent(SystemComponent):
    """Component managing units."""

    def __init__(self, config_dir: str, component_manager=None):
        super().__init__(config_dir, component_manager)
        self._ast_manager = HyAST()
        self._unit_manager = UnitManager()
        self._loader = UnitLoader(self._unit_manager)
        self._units_dir = os.path.join(self._config_dir, "units")

    def load(self) -> None:
        """Load units from all Hy files in the units directory"""
        if self._loaded:
            return

        # Create units directory if it doesn't exist
        if not os.path.exists(self._units_dir):
            os.makedirs(self._units_dir)

        # Check if there are any files in the directory
        unit_files = [f for f in os.listdir(self._units_dir) if f.endswith(".hy")]

        # If no files in the units directory, check for the old units.hy file
        old_units_file = Path(self._config_dir) / "units.hy"
        if not unit_files and old_units_file.exists():
            unit_files = [str(old_units_file)]
            is_old_format = True
        else:
            is_old_format = False

        if not unit_files:
            self._loaded = True
            return

        try:
            # Create context
            context = LoaderContext(
                config_dir=self._config_dir, variables=self._items  # Pass existing items if any
            )

            # Process all unit files
            all_items = {}

            for filename in unit_files:
                file_path = (
                    os.path.join(self._units_dir, filename) if not is_old_format else filename
                )
                self.logger.debug(f"Loading units from {file_path}")

                try:
                    # Parse file into nodes
                    nodes = self._ast_manager.parse_file(str(file_path))

                    # Process nodes using loader
                    items = self._loader.process(nodes, context)

                    # Add to all items
                    all_items.update(items)

                except Exception as e:
                    self.logger.error(f"Error loading units from {file_path}: {e}")
                    # Continue with other files even if one fails

            self._items = all_items

            # Update manager's items
            self._unit_manager._items = self._items

            self._loaded = True

        except Exception as e:
            self.logger.error(f"Error loading units: {e}")
            raise

    def save(self) -> None:
        """Save units to appropriate files in the units directory"""
        # Ensure units directory exists
        if not os.path.exists(self._units_dir):
            os.makedirs(self._units_dir)

        # Get the unit plugin
        plugin = plugin_registry.get_node_plugin("def-unit")
        if not plugin:
            raise ValueError("Unit plugin not found")

        # Group units by category
        units_by_category = {}
        for key, unit in self._items.items():
            # Get category from unit or use default
            category = getattr(unit, "category", None)
            if not category:
                # Try to determine category from groups
                if unit.groups and "fixed" in unit.groups:
                    category = "fixed_units"
                elif unit.groups and "calendar" in unit.groups:
                    category = "calendar_units"
                else:
                    category = "default"

            if category not in units_by_category:
                units_by_category[category] = []
            units_by_category[category].append(unit)

        # Save each category to its own file
        for category, units in units_by_category.items():
            file_path = os.path.join(self._units_dir, f"{category}.hy")

            # Create nodes for each unit of this category
            nodes = []
            for unit in sorted(units, key=lambda u: u.name):
                # Create expression parts
                expr_parts = [hy.models.Symbol("def-unit"), hy.models.Symbol(unit.label)]

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

            # Convert to Hy code and save
            content = self._ast_manager.to_hy(nodes)
            with open(file_path, "w") as f:
                f.write(content)

            self.logger.debug(f"Saved {len(units)} units to {file_path}")

    def get_unit(self, label: str) -> Any:
        """Get a unit by label"""
        return self._unit_manager.get(label)

    def get_all_units(self) -> Dict[str, Any]:
        """Get all units"""
        return self._unit_manager.get_all()

    def get_units_by_group(self, group):
        """Get all units"""
        return self._unit_manager.get_units_by_group(group)

    def get_units_by_groups(self, groups, match_all: bool = False):
        """Get all units"""
        return self._unit_manager.get_units_by_groups(groups, match_all)

    def add_unit(self, unit: Unit) -> None:
        """Add a unit."""
        self._unit_manager.add(unit.label, unit)

    def remove_unit(self, label: str) -> None:
        """Remove a unit by label."""
        self._unit_manager.remove(label)

    def create_unit(
        self, label: str, name: str, value: Decimal, groups: Optional[List[str]] = None
    ) -> Unit:
        """Create a new unit."""
        return self._unit_manager.create(label=label, name=name, value=value, groups=groups)

    def convert(self, args: Namespace):
        return self._unit_manager.convert_units(args)

    def print(self, args: Namespace):
        return self._unit_manager.print(args)
