import os
from decimal import Decimal
from typing import Any, Dict, List, Optional

from utms.core.loaders.fixed_unit import FixedUnitLoader
from utms.core.managers.fixed_unit import FixedUnitManager
from utms.core.models.fixed_unit import FixedUnit
from utms.loaders.base import LoaderContext
from utms.resolvers import HyAST

from .base import SystemComponent


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

        fixed_units_file = os.path.join(self._config_dir, "fixed_units.hy")
        if os.path.exists(fixed_units_file):
            try:
                # Parse file into nodes
                nodes = self._ast_manager.parse_file(fixed_units_file)

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
        fixed_units_file = os.path.join(self._config_dir, "fixed_units.hy")
        self._fixed_unit_manager.save(fixed_units_file)

    def get_unit(self, label: str) -> Any:
        """Get a fixed unit by label"""
        return self._fixed_unit_manager.get(label)

    def get_all_units(self) -> Dict[str, Any]:
        """Get all fixed units"""
        return self._fixed_unit_manager.get_all()

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
