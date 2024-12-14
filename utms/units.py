"""
Time Unit Management Module
===========================

This module provides a class, `TimeUnitManager`, for managing time units. It allows users to
add, retrieve, and sort time units by their values (in seconds), as well as print the units
and generate conversion tables for easy comparison.

Classes:
--------
- `TimeUnitManager`: Handles the addition, management, and retrieval of time units.

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
from time_unit_manager import TimeUnitManager

# Initialize the manager
manager = TimeUnitManager()

# Add time units
manager.add_time_unit("Second", "s", Decimal("1"))
manager.add_time_unit("Minute", "m", Decimal("60"))
manager.add_time_unit("Hour", "h", Decimal("3600"))

# Print all units
manager.print_units()

# Print a conversion table centered around seconds
manager.print_conversion_table("s", num_columns=2, num_rows=5)
"""

from decimal import Decimal
from typing import Dict, Union

from colorama import Fore, Style, init

init()


def format_value(
    value: Decimal, threshold: Decimal = Decimal("1e7"), small_threshold: Decimal = Decimal("0.001")
) -> str:
    """
    Format a numeric value based on specified thresholds, using conditional formatting.

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
    # Handle values smaller than small_threshold (0.001)
    if abs(value) < small_threshold:
        return f"{Fore.RED}{Style.BRIGHT}{value:.3e}{Style.RESET_ALL}".ljust(
            33
        )  # Scientific notation with 3 decimal places
    # Handle values smaller than threshold (1e7) but larger than small_threshold
    if abs(value) < threshold:
        if value == value.to_integral_value():
            return f"{Fore.GREEN}{Style.BRIGHT}{value:.0f}{Style.RESET_ALL}".ljust(
                33
            )  # Integer formatting
        if value > 1:
            return f"{Fore.GREEN}{Style.BRIGHT}{value:.5f}{Style.RESET_ALL}".ljust(
                33
            )  # Fixed-point notation with 5 decimal places
        if value == value.quantize(small_threshold):
            return f"{Fore.RED}{Style.BRIGHT}{value:.3f}{Style.RESET_ALL}".ljust(
                33
            )  # Fixed-point notation with 3 decimal places if there are no further digits
        return f"{Fore.RED}{Style.BRIGHT}{value:.5f}{Style.RESET_ALL}".ljust(
            33
        )  # Fixed-point notation with 5 decimal places
    if abs(value) >= threshold:
        return f"{Fore.GREEN}{Style.BRIGHT}{value:.3e}{Style.RESET_ALL}".ljust(
            33
        )  # Scientific notation with 3 decimal places
    return f"{Fore.GREEN}{Style.BRIGHT}{value:.3f}{Style.RESET_ALL}".ljust(
        33
    )  # Fixed-point notation with 3 decimal places


class TimeUnitManager:
    """
    A class to manage time units, allowing adding new units, sorting
    by value, and accessing them by abbreviation.
    """

    def __init__(self) -> None:
        self._units: Dict[str, Dict[str, Union[Decimal, str]]] = {}

    def add_time_unit(self, full_name: str, abbreviation: str, value: Decimal) -> None:
        """
        Adds a new time unit to the manager and ensures the units are sorted by value.

        Args:
            full_name (str): The full name of the time unit.
            abbreviation (str): The abbreviation of the time unit.
            value (Decimal): The value of the unit in seconds.
        """
        key = abbreviation
        self._units[key] = {
            "full_name": full_name,
            "value": value,
        }
        self._sort_units()

    def _sort_units(self) -> None:
        """
        Sort the units by their value (in seconds).
        """
        self._units = dict(sorted(self._units.items(), key=lambda item: item[1]["value"]))

    def get_value(self, abbreviation: str) -> Decimal:
        """
        Get a unit value by its abbreviation.

        Args:
            abbreviation (str): The abbreviation of the time unit.

        Returns:
            value: A Decimal value of the unit
        """
        unit = self.get_unit(abbreviation)
        if unit:
            return Decimal(unit["value"])
        raise ValueError(f"No unit with abbreviation {unit} defined")

    def get_unit(self, abbreviation: str) -> Union[Dict[str, Union[Decimal, str]], None]:
        """
        Get a time unit by its abbreviation.

        Args:
            abbreviation (str): The abbreviation of the time unit.

        Returns:
            dict: A dictionary containing 'full_name' and 'value' of the time unit.
        """
        return self._units.get(abbreviation, None)

    def get_all_units(self) -> Dict[str, Dict[str, Union[Decimal, str]]]:
        """
        Get all the time units stored in the manager.

        Returns:
            dict: A dictionary with abbreviations as keys and unit information as values.
        """
        return self._units

    def print_units(self) -> None:
        """
        Prints all time units sorted by their value in seconds.
        """
        for key, unit in self._units.items():
            print(f"{unit['full_name']} ({key}): {unit['value']} seconds")

    def print_conversion_table(
        self, center_unit: str, num_columns: int = 5, num_rows: int = 100
    ) -> None:
        """
        Prints a table of time unit conversions centered around a specific unit.

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
            + "".join(
                f"{self._units[key]['full_name']} ({key})".ljust(20) for key in displayed_columns
            )
        )
        print("-" * (25 + len(displayed_columns) * 20))

        # Print conversion table
        for row_abbrev in displayed_rows:
            conversions = {
                col_abbrev: self.get_value(row_abbrev) / self.get_value(col_abbrev)
                for col_abbrev in displayed_columns
                if self.get_value(row_abbrev) and self.get_value(col_abbrev)
            }
            # conversions = {}
            # for col_abbrev in displayed_columns:
            #     value1 = self.get_value(row_abbrev)
            #     value2 = self.get_value(col_abbrev)
            #     if value1 and value2:
            #         conversions[col_abbrev] = value1 / value2

            print(
                f"{self._units[row_abbrev]['full_name']} ({row_abbrev})".ljust(25)
                + "".join(
                    f"{format_value(conversions[col_abbrev])}" for col_abbrev in displayed_columns
                )
            )
