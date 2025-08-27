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
from utms.utms_types.field.types import TypedValue

class UnitComponent(SystemComponent):
    """Component managing units."""

    def __init__(self, config_dir: str, component_manager=None):
        super().__init__(config_dir, component_manager)
        self._ast_manager = HyAST()
        self._unit_manager = UnitManager()
        self._loader = UnitLoader(self._unit_manager)
        self._global_units_dir = os.path.join(self._config_dir, "global", "units")
        config_component = self.get_component("config")
        if not config_component.is_loaded(): config_component.load()
        active_user_config = config_component.get_config("active-user")
        self._user_units_dir = None
        if active_user_config and (active_user := active_user_config.get_value()):
            user_root = os.path.join(self._config_dir, "users", active_user)
            self._user_units_dir = os.path.join(user_root, "units")
        else:
            self.logger.warning("No active user; only global units will be loaded.")

    def load(self) -> None:
        """Load units from global and then user directories"""
        if self._loaded:
            return

        def _process_dir(path, context):
            if not (path and os.path.isdir(path)):
                return
            os.makedirs(path, exist_ok=True)
            for filename in os.listdir(path):
                if not filename.endswith(".hy"): continue
                file_path = os.path.join(path, filename)
                try:
                    nodes = self._ast_manager.parse_file(str(file_path))
                    self._items.update(self._loader.process(nodes, context))
                except Exception as e:
                    self.logger.error(f"Error loading units from {file_path}: {e}")

        self._unit_manager.clear()

        self._items = self._unit_manager.get_all()

        variables_component = self.get_component("variables")
        variables = {}
        if variables_component:
            for name, var_model in variables_component.items():
                if hasattr(var_model, 'value') and isinstance(var_model.value, TypedValue):
                    py_value = var_model.value.value
                    variables[name] = py_value
                    if '-' in name:
                        variables[name.replace('-', '_')] = py_value
        context = LoaderContext(config_dir=self._config_dir, variables=variables)

        _process_dir(self._global_units_dir, context) 
        _process_dir(self._user_units_dir, context)   

        self._loaded = True

    def save(self) -> None:
        """Save units to appropriate files in the units directory"""
        if not self._user_units_dir:
            self.logger.error("Cannot save units: No active user directory is configured.")
            return

        os.makedirs(self._user_units_dir, exist_ok=True)

        plugin = plugin_registry.get_node_plugin("def-unit")
        if not plugin:
            raise ValueError("Unit plugin not found")

        units_by_category = {}
        for key, unit in self._items.items():
            category = getattr(unit, "category", None)
            if not category:
                if unit.groups and "fixed" in unit.groups:
                    category = "fixed_units"
                elif unit.groups and "calendar" in unit.groups:
                    category = "calendar_units"
                else:
                    category = "default"

            if category not in units_by_category:
                units_by_category[category] = []
            units_by_category[category].append(unit)

        for category, units in units_by_category.items():
            file_path = os.path.join(self._user_units_dir, f"{category}.hy")
            nodes = []
            for unit in sorted(units, key=lambda u: u.name):
                expr_parts = [hy.models.Symbol("def-unit"), hy.models.Symbol(unit.label)]
                properties = [
                    hy.models.Expression([hy.models.Symbol("name"), hy.models.String(unit.name)]),
                    hy.models.Expression(
                        [hy.models.Symbol("value"), hy.models.Float(float(unit.value))]
                    ),
                ]
                if unit.groups:
                    properties.append(
                        hy.models.Expression(
                            [
                                hy.models.Symbol("groups"),
                                hy.models.List([hy.models.String(group) for group in unit.groups]),
                            ]
                        )
                    )
                expr_parts.extend(properties)
                expr = hy.models.Expression(expr_parts)
                nodes.append(plugin.parse(expr))
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
