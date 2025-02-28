from argparse import Namespace
from decimal import Decimal
from typing import Dict, List, Optional, Union

from utms.utils import format_value
from utms.utms_types import FixedUnitManagerProtocol

from ..models.fixed_unit import FixedUnit
from utms.core.time.plt import seconds_to_hplt, seconds_to_pplt
from .base import BaseManager


class FixedUnitManager(BaseManager[FixedUnit], FixedUnitManagerProtocol):
    """Manages fixed units with their properties and relationships."""

    def create(
        self, label: str, name: str, value: Union[str, Decimal], groups: Optional[List[str]] = None
    ) -> FixedUnit:
        """Create a new fixed unit."""
        if label in self._items:
            raise ValueError(f"Unit with label '{label}' already exists")

        fixed_unit = FixedUnit(label=label, name=name, value=Decimal(value), groups=groups or [])
        self.add(label, fixed_unit)
        self._sort_units()
        return fixed_unit

    def _sort_units(self) -> None:
        """Sort the units by their value (in seconds)."""
        self._items = dict(sorted(self._items.items(), key=lambda item: item[1].value))

    def get_units_by_group(self, group: str) -> List[FixedUnit]:
        """Get all units belonging to a specific group."""
        return [unit for unit in self._items.values() if group in unit.groups]

    def get_units_by_groups(self, groups: List[str], match_all: bool = False) -> List[FixedUnit]:
        """Get units belonging to multiple groups."""
        if match_all:
            return [
                unit
                for unit in self._items.values()
                if all(group in unit.groups for group in groups)
            ]
        else:
            return [
                unit
                for unit in self._items.values()
                if any(group in unit.groups for group in groups)
            ]

    def serialize(self) -> Dict[str, Dict[str, Union[str, Decimal, List[str]]]]:
        """Convert units to serializable format."""
        return {
            label: {"name": unit.name, "value": unit.value, "groups": unit.groups}
            for label, unit in self._items.items()
        }

    def deserialize(self, data: Dict[str, Dict[str, Union[str, Decimal, List[str]]]]) -> None:
        """Load units from serialized data."""
        self.clear()
        for label, unit_data in data.items():
            self.create(
                label=label,
                name=unit_data["name"],
                value=unit_data["value"],
                groups=unit_data.get("groups", []),
            )

    def convert_units(self, args: Namespace) -> None:
        """Convert a given value from one unit to all other units and print the results.

        Args:
            args: Namespace containing:
                - value: The value to be converted
                - source_unit: The label of the unit of the input value
                - target_unit: Optional specific unit to convert to
                - raw: Whether to output raw values
                - precision: Number of decimal places for output
        """
        decimal_value = Decimal(args.value)
        if args.source_unit not in self._items:
            raise ValueError(f"Input unit '{args.source_unit}' not found in time units.")

        input_unit = self._items[args.source_unit]

        if not args.raw:
            print(f"Converting {args.value} {args.source_unit}:")
            print("-" * 50)

        precision = args.precision if args.precision is not None else 5

        if not args.target_unit:
            for label, unit in self._items.items():
                converted_value = input_unit.convert_to(unit, decimal_value)
                if args.raw:
                    print(f"{converted_value:.{precision}f}")
                else:
                    print(f"{unit.name} ({label}):".ljust(25) + f"{format_value(converted_value)}")
        else:
            target_unit = self._items[args.target_unit]
            converted_value = input_unit.convert_to(target_unit, decimal_value)
            if args.raw:
                print(f"{converted_value:.{precision}f}")
            else:
                print(
                    f"{target_unit.name} ({args.target_unit}):".ljust(25)
                    + f"{format_value(converted_value)}"
                )

    def print(self, args: Namespace) -> None:
        """Print all fixed units sorted by their value in seconds."""
        plt = bool(getattr(args, "plt", False))

        if plt:
            print(
                "Unit name (abbr):".ljust(25)
                + "Value".ljust(20)
                + "hPLT".ljust(20)
                + "pPLT".ljust(20)
            )
        else:
            print("Unit name (abbr):".ljust(25) + "Value".ljust(20))

        for unit in sorted(self._items.values(), key=lambda u: u.value):
            if plt:
                print(
                    f"{unit.name} ({unit.label}):".ljust(25)
                    + f"{format_value(unit.value)}"
                    + f"{seconds_to_hplt(unit.value):.5f}".ljust(20)
                    + f"{seconds_to_pplt(unit.value):.5f}".ljust(20)
                )
            else:
                print(f"{unit.name} ({unit.label}):".ljust(25) + f"{format_value(unit.value)}")
