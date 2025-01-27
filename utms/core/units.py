"""
Unit Management Module
===========================

This module provides a class, `UnitManager`, for managing time units. It allows users to
add, retrieve, and sort time units by their values (in seconds), as well as print the units
and generate conversion tables for easy comparison.

Classes:
--------
- `UnitManager`: Handles the addition, management, and retrieval of time units.

Dependencies:
-------------
- `decimal.Decimal`: For precise arithmetic with time unit values.
- `utms.utils.format_value`: A utility function for formatting values.

Features:
---------
1. Add new time units with a full name, abbreviation, and value (in seconds).
2. Retrieve time unit values or details by their abbreviation.
3. Retrieve all stored time units in a sorted dictionary.
4. Print time units and their details.
5. Generate and print a conversion table centered around a specific time unit.

Usage:
------
```python
from decimal import Decimal
from time_unit_manager import UnitManager

# Initialize the manager
manager = UnitManager()

# Add time units
manager.add_unit("Second", "s", Decimal("1"))
manager.add_unit("Minute", "m", Decimal("60"))
manager.add_unit("Hour", "h", Decimal("3600"))

# Print all units
manager.print_units()

# Print a conversion table centered around seconds
manager.print_conversion_table("s", num_columns=2, num_rows=5)
"""

import argparse
from decimal import Decimal
from typing import Dict, Iterator, Optional, Union

from colorama import Fore, Style

from utms.utms_types import UnitManagerProtocol, UnitProtocol

from .plt import seconds_to_hplt, seconds_to_pplt


def format_value(
    value: Decimal, threshold: Decimal = Decimal("1e7"), small_threshold: Decimal = Decimal("0.001")
) -> str:
    """Format a numeric value based on specified thresholds, using conditional
    formatting.

    The function formats the value based on its magnitude, and applies different styles
    depending on whether the value is above or below specific thresholds.

    Args:
        value (Decimal): The numeric value to format.
        threshold (Decimal, optional): The threshold above which
        scientific notation is used. Defaults to 1e7.
        small_threshold (Decimal, optional): The threshold below which
        scientific notation with 3 decimal places is used. Defaults to
        0.001.

    Returns:
        str: The formatted string representation of the value with appropriate styles applied.

    Formatting Rules:
        - Values smaller than `small_threshold` are formatted in
          scientific notation with 3 decimal places in red.
        - Values larger than `small_threshold` but smaller than `threshold`:
            - Integer values are formatted with no decimal places in green.
            - Values greater than 1 are formatted with 5 decimal places in green.
            - Values close to zero are formatted with 3 or 5 decimal
              places in red depending on precision.
        - Values greater than or equal to `threshold` are formatted in
          scientific notation with 3 decimal places in green.
        - All formatting is left-aligned in a 33-character wide field.

    Example:
        >>> format_value(123456.789)
        '\x1b[32m\x1b[1m123456.78900\x1b[39m\x1b[22m'  # Example output with a large value

        >>> format_value(0.000000123)
        '\x1b[31m\x1b[1m1.230e-07\x1b[39m\x1b[22m'  # Example output for a small value
    """

    def apply_red_style(value: str) -> str:
        """Applies bright red style to the formatted value."""
        return f"{Style.BRIGHT}{Fore.RED}{value}{Style.RESET_ALL}"

    def apply_green_style(value: str) -> str:
        """Applies bright green style to the formatted value."""
        return f"{Style.BRIGHT}{Fore.GREEN}{value}{Style.RESET_ALL}"

    # Handle absolute value less than small_threshold
    if abs(value) < small_threshold:
        formatted_value = apply_red_style(
            f"{value:.3e}"
        )  # Scientific notation with 3 decimal places
    # Handle values smaller than threshold (1e7) but larger than small_threshold
    elif abs(value) < threshold:
        if value == value.to_integral_value():
            formatted_value = apply_green_style(f"{value:.0f}")  # Integer formatting
        elif value > 1:
            formatted_value = apply_green_style(
                f"{value:.5f}"
            )  # Fixed-point notation with 5 decimal places
        elif value == value.quantize(small_threshold):
            formatted_value = apply_red_style(
                f"{value:.3f}"
            )  # Fixed-point with 3 decimal places if no further digits
        else:
            formatted_value = apply_red_style(
                f"{value:.5f}"
            )  # Fixed-point notation with 5 decimal places
    # Handle absolute value greater than or equal to threshold
    elif abs(value) >= threshold:
        formatted_value = apply_green_style(
            f"{value:.3e}"
        )  # Scientific notation with 3 decimal places
    else:
        formatted_value = apply_green_style(
            f"{value:.3f}"
        )  # Fixed-point notation with 3 decimal places

    return formatted_value.ljust(33)


class Unit(UnitProtocol):
    """Represents a time unit with a full name, abbreviation, and value in
    seconds. Provides methods for comparisons, conversions, and formatting.

    Attributes:
        name (str): The full name of the time unit.
        abbreviation (str): The abbreviation of the time unit.
        value (Decimal): The value of the time unit in seconds.
    """

    def __init__(self, name: str, abbreviation: str, value: Decimal) -> None:
        """Initializes a Unit instance.

        Args:
            name (str): The full name of the time unit.
            abbreviation (str): The abbreviation of the time unit.
            value (Decimal): The value of the time unit in seconds.
        """
        self._name = name
        self._abbreviation = abbreviation
        self._value = value

    @property
    def name(self) -> str:
        return self._name

    @property
    def abbreviation(self) -> str:
        return self._abbreviation

    @property
    def value(self) -> Decimal:
        return self._value

    def __repr__(self) -> str:
        """Provides a string representation of the Unit instance.

        Returns:
            str: A string representation of the unit.
        """
        return f"Unit(name={self.name}, abbreviation={self.abbreviation}, value={self.value})"

    def __eq__(self, other: object) -> bool:
        """Compares two Unit instances for equality based on value.

        Args:
            other (object): The other object to compare to.

        Returns:
            bool: True if both units are equal, False otherwise.
        """
        if isinstance(other, Unit):
            return self.value == other.value
        return False

    def __lt__(self, other: object) -> bool:
        """Compares two Unit instances for less-than based on value.

        Args:
            other (object): The other object to compare to.

        Returns:
            bool: True if this unit is less than the other unit, False otherwise.
        """
        if isinstance(other, Unit):
            return self.value < other.value
        return False

    def convert_to(self, other: "Unit", value: Decimal) -> Decimal:
        """Converts a value from this unit to another unit.

        Args:
            other (Unit): The unit to convert to.
            value (Decimal): The value to convert.

        Returns:
            Decimal: The converted value in the new unit.
        """
        # Conversion formula: value_in_new_unit = value_in_current_unit * (self.value / other.value)
        return value * (self.value / other.value)

    def __str__(self) -> str:
        """Provides a human-readable string for the unit.

        Returns:
            str: A string representation of the unit.
        """
        return f"{self.name} ({self.abbreviation}): {self.value} seconds"


class UnitManager(UnitManagerProtocol):
    """A class to manage time units, allowing adding new units, sorting by
    value, and accessing them by abbreviation."""

    def __init__(self) -> None:
        self._units: Dict[str, Unit] = {}

    def add_unit(self, name: str, abbreviation: str, value: Decimal) -> None:
        """Adds a new time unit to the manager and ensures the units are sorted
        by value.

        Args:
            name (str): The full name of the time unit.
            abbreviation (str): The abbreviation of the time unit.
            value (Decimal): The value of the unit in seconds.
        """
        new_unit = Unit(name, abbreviation, value)
        self._units[abbreviation] = new_unit
        self._sort_units()

    def _sort_units(self) -> None:
        """Sort the units by their value (in seconds)."""
        self._units = dict(sorted(self._units.items(), key=lambda item: item[1].value))

    def get_value(self, abbreviation: str) -> Decimal:
        """Get a unit value by its abbreviation.

        Args:
            abbreviation (str): The abbreviation of the time unit.

        Returns:
            value: A Decimal value of the unit
        """
        unit = self.get_unit(abbreviation)
        if unit:
            return unit.value
        raise ValueError(f"No unit with abbreviation {unit} defined")

    def get_unit(self, abbreviation: str) -> Optional[Unit]:
        """Get a time unit by its abbreviation.

        Args:
            abbreviation (str): The abbreviation of the time unit.

        Returns:
            dict: A dictionary containing 'name' and 'value' of the time unit.
        """
        return self._units.get(abbreviation)

    def get_all_units(self) -> Dict[str, Unit]:
        """Get all the time units stored in the manager.

        Returns:
            dict: A dictionary with abbreviations as keys and unit information as values.
        """
        return self._units

    def __iter__(self) -> Iterator[str]:
        """Returns an iterator over the abbreviations of all time units.

        :return: An iterator of unit abbreviations.
        """
        return iter(self._units)

    def __getitem__(self, index: Union[int, str]) -> Unit:
        """Makes the class subscriptable by allowing access via abbreviation or
        index.

        Args:
            index (int or str): The abbreviation or index of the unit.

        Returns:
            dict: A dictionary containing 'name' and 'value' of the time unit.

        Raises:
            KeyError: If the abbreviation does not exist.
            IndexError: If the index is out of range.
        """
        if isinstance(index, int):  # Index-based access
            try:
                return list(self._units.values())[index]
            except IndexError as exc:
                raise IndexError(f"Index {index} is out of range.") from exc
        else:
            if index in self._units:
                return self._units[index]
            raise KeyError(f"Unit with abbreviation '{index}' not found.")

    def __len__(self) -> int:
        """Returns the number of time units in the manager.

        :return: The number of units.
        """
        return len(self._units)

    def print(self, args: argparse.Namespace) -> None:
        """Prints all time units sorted by their value in seconds."""
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
        for unit in self._units.values():
            if plt:
                print(
                    f"{unit.name} ({unit.abbreviation}):".ljust(25)
                    + f"{format_value(unit.value)}"
                    + f"{seconds_to_hplt(unit.value):.5f}".ljust(20)
                    + f"{seconds_to_pplt(unit.value):.5f}".ljust(20)
                )
            else:
                print(
                    f"{unit.name} ({unit.abbreviation}):".ljust(25) + f"{format_value(unit.value)}"
                )

    def print_conversion_table(
        self, center_unit: str, num_columns: int = 5, num_rows: int = 100
    ) -> None:
        """Prints a table of time unit conversions centered around a specific
        unit.

        Args:
            center_unit (str): The abbreviation of the unit around
                which the table will be centered.
            num_units (int): The number of units to display on either
                side of the center unit. Defaults to 5.

        Example:
            manager.print_conversion_table("s", 3)
            This will print a table centered around "s", showing 3 units to the left and right.
        """
        # Get all unit abbreviations
        unit_keys = list(self._units.keys())

        if center_unit not in unit_keys:
            raise ValueError(f"Center unit '{center_unit}' not found in time units.")

        # Find the index of the center unit
        center_index = unit_keys.index(center_unit)

        # Determine the range of units to display for columns (header)
        col_start_index = max(0, center_index - num_columns)
        col_end_index = min(len(unit_keys), center_index + num_columns + 1)
        displayed_columns = unit_keys[col_start_index:col_end_index]

        # Determine the range of units to display for rows
        row_start_index = max(0, center_index - num_rows)
        row_end_index = min(len(unit_keys), center_index + num_rows + 1)
        displayed_rows = unit_keys[row_start_index:row_end_index]

        # Print header
        print(
            "Time Unit".ljust(25)
            + "".join(f"{self._units[key].name} ({key})".ljust(20) for key in displayed_columns)
        )
        print("-" * (25 + len(displayed_columns) * 20))

        # Print conversion table
        for row_abbrev in displayed_rows:
            conversions = {
                col_abbrev: self._units[row_abbrev].convert_to(
                    self._units[col_abbrev], Decimal("1")
                )
                for col_abbrev in displayed_columns
            }

            print(
                f"{self._units[row_abbrev].name} ({row_abbrev})".ljust(25)
                + "".join(
                    f"{format_value(conversions[col_abbrev])}" for col_abbrev in displayed_columns
                )
            )

    def convert_units(self, args: argparse.Namespace) -> None:
        """Convert a given value from one unit to all other units and print the
        results.

        Args:
            value (Decimal): The value to be converted.
            input_unit (str): The abbreviation of the unit of the input value.

        Raises:
            ValueError: If the input unit is not found in the manager.
        """
        decimal_value = Decimal(args.value)
        if args.source_unit not in self._units:
            raise ValueError(f"Input unit '{args.source_unit}' not found in time units.")

        input_unit_instance = self._units[args.source_unit]

        if not args.raw:
            print(f"Converting {args.value} {args.source_unit}:")
            print("-" * 50)

        precision = args.precision if args.precision is not None else 5

        if not args.target_unit:
            for abbrev, unit_instance in self._units.items():
                converted_value = input_unit_instance.convert_to(unit_instance, decimal_value)
                if args.raw:
                    print(f"{converted_value:.{precision}f}")
                else:
                    print(
                        f"{unit_instance.name} ({abbrev}):".ljust(25)
                        + f"{format_value(converted_value)}"
                    )
        else:
            converted_value = input_unit_instance.convert_to(
                self._units[args.target_unit], decimal_value
            )
            if args.raw:
                print(f"{converted_value:.{precision}f}")
            else:
                print(
                    f"{self._units[args.target_unit].name} ({args.target_unit}):".ljust(25)
                    + f"{format_value(converted_value)}"
                )
