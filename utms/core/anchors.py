"""
Module: Anchor Management for Time Anchors

This module provides utilities for creating and managing time anchors.
Time anchors are representations of specific points in time or numerical values
associated with a precision, which can be accessed and organized efficiently.

The module includes two main classes:

1. **Anchor**:
   - Represents a single time anchor with a name, value, and precision.
   - Designed for simplicity, allowing direct access to attributes such as `name`,
     `value`, and `precision`.

2. **AnchorManager**:
   - Manages multiple time anchors, enabling functionalities such as adding anchors,
     iterating over them, and accessing anchors by index or label.
   - Supports anchors defined by both `datetime` and `Decimal` values, with customizable precision.

**Features**:
- Add datetime or decimal-based anchors with specific labels and precision.
- Retrieve anchors by label or numerical index.
- Iterate over all anchors managed by the class.
- Handle edge cases for ancient dates (adjusting for negative timestamps).
- Ensure type safety and robust exception handling for invalid access.

**Dependencies**:
- `datetime` and `timezone`: For working with time-based anchors.
- `decimal.Decimal`: To ensure precise numerical representation for anchor values.
- `utms.constants`: Provides constants used for calculations, such as `SECONDS_IN_YEAR`.

**Example Usage**:

```python
from datetime import datetime, timezone
from decimal import Decimal
from utms.anchor_manager import AnchorManager

# Initialize an AnchorManager
manager = AnchorManager()

# Add a datetime anchor
manager.add_datetime_anchor(
    name="Epoch Start",
    label="epoch",
    value=datetime(1970, 1, 1, tzinfo=timezone.utc)
)

# Add a decimal anchor
manager.add_decimal_anchor(
    name="Custom Anchor",
    label="custom",
    value=Decimal("12345.6789"),
    precision=Decimal("0.001")
)

# Access anchors by label
epoch_anchor = manager["epoch"]

# Iterate through all anchors
for anchor in manager:
    print(anchor.name, anchor.value, anchor.precision)

# Get the number of anchors
print(len(manager))
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, Iterator, List, NamedTuple, Optional, Union

from colorama import Fore, Style

from utms.utils import value_to_decimal

from . import constants
from .units import UnitManager


class AnchorConfig(NamedTuple):
    """Configuration for defining a time anchor.

    This class encapsulates the essential attributes needed to configure a time anchor,
    including its full name, value, precision, and breakdown structure.

    Attributes
    ----------
    name : str
        The full descriptive name of the anchor.
    value : Decimal
        The numeric value associated with the anchor.
    precision : Decimal
        The precision to use for calculations involving the anchor.
    breakdowns : List[List[str]]
        A nested list defining the breakdown structure for the anchor, where each sublist
        represents a level of detail (e.g., ["hours", "minutes", "seconds"]).
    """

    label: str
    name: str
    value: Union[Decimal, datetime]
    breakdowns: Optional[List[List[str]]] = None
    groups: Optional[List[str]] = None
    precision: Optional[Decimal] = None


class Anchor:
    """Represents a single time anchor with a full name, value, precision, and
    associated breakdown formats.

    This class provides functionality to break down a total duration in seconds into a
    human-readable format using a configurable set of units. It allows the conversion of a given
    duration into various time units (e.g., hours, minutes, seconds) while considering the precision
    for breakdown.

    Attributes:
        name (str): The full name of the anchor (e.g., "Total Time").
        value (Decimal): The value associated with the anchor (e.g., total time value in seconds).
        precision (Decimal): The precision threshold for unit breakdown (e.g., the smallest unit for
        display).
        breakdowns (List[List[str]]): A list of breakdown formats, each containing a list of unit
                                      abbreviations (e.g., [["h", "m", "s"]]).

    Methods:
        breakdown(total_seconds: Decimal, units: UnitManager) -> str:
            Breaks down a given total duration (in seconds) into the configured units and returns a
            formatted string representing the breakdown.

        _apply_color(value: str, color: str = Fore.BLUE) -> str:
            Applies the specified color style to the given value.

        _format_breakdown_entry(count: Union[int, Decimal], unit: str) -> str:
            Formats a single breakdown entry, ensuring proper string formatting and color styling.

        _calculate_breakdown(total_seconds: Decimal, breakdown_units: List[str], units: UnitManager)
        -> List[str]:
            Calculates the breakdown for a given set of units based on the total duration and
            precision.
    """

    def __init__(self, anchor_config: AnchorConfig) -> None:
        """Create the Anchor object with its parameters inside."""
        self.label = anchor_config.label
        self.name = anchor_config.name
        self.value = value_to_decimal(anchor_config.value)
        self.precision = anchor_config.precision or constants.STANDARD_PRECISION
        self.breakdowns = anchor_config.breakdowns or constants.STANDARD_BREAKDOWN
        self.groups = anchor_config.groups or []

    def _format_breakdown_entry(self, count: Union[int, Decimal], unit: str) -> str:
        """Formats a single breakdown entry."""

        def apply_blue_color(value: str) -> str:
            """Applies the specified color style to the given value."""
            return f"{Fore.BLUE}{value}{Style.RESET_ALL}"

        formatted_count = (
            f"{count:.3f}" if isinstance(count, Decimal) and count % 1 != 0 else str(count)
        )
        return f"{formatted_count} {apply_blue_color(unit)}".ljust(25)

    def _calculate_breakdown(
        self, total_seconds: Decimal, breakdown_units: List[str], units: "UnitManager"
    ) -> List[str]:
        """Calculates the breakdown for a given list of units."""
        remaining_seconds = Decimal(total_seconds)
        breakdown = []

        for i, unit_abbreviation in enumerate(breakdown_units):
            unit = units.get_unit(unit_abbreviation)
            if not unit:
                continue

            unit_count: Union[int, Decimal]
            unit_value = Decimal(unit.value)

            if i < len(breakdown_units) - 1:
                unit_count = int(remaining_seconds // unit_value)
                remaining_seconds %= unit_value
            else:
                unit_count = remaining_seconds / unit_value

            if unit_count > 0 or i == len(breakdown_units) - 1:
                breakdown.append(self._format_breakdown_entry(unit_count, unit_abbreviation))

        return breakdown

    def print(self) -> None:
        """Print details of a single anchor by label."""

        def apply_green_color(value: str) -> str:
            """Applies the specified color style to the given value."""
            return f"{Style.BRIGHT}{Fore.GREEN}{value}{Style.RESET_ALL}"

        print(f"{apply_green_color('Label')}: {self.label}")
        print(f"{apply_green_color('Name')}: {self.name}")
        print(f"{apply_green_color('Value')}: {self.value:.3f}")
        print(f"{apply_green_color('Groups')}: {', '.join(self.groups)}")
        print(f"{apply_green_color('Precision')}: {self.precision:.3e}")
        print(f"{apply_green_color('Breakdowns')}:")
        for breakdown in self.breakdowns:
            print(f"  - {', '.join(breakdown)}")
        print("-" * 50)

    def breakdown(self, total_seconds: Decimal, units: "UnitManager") -> str:
        """Breaks down a duration in seconds into multiple unit formats.

        Args:
            total_seconds (Decimal): Total duration in seconds.
            units (UnitManager): UnitManager instance for unit details.

        Returns:
            str: A formatted string representing the breakdown.
        """
        output = []

        prefix = (
            Fore.RED + Style.BRIGHT + "  - " + Style.RESET_ALL
            if total_seconds < 0
            else Fore.GREEN + Style.BRIGHT + "  + " + Style.RESET_ALL
        )
        total_seconds = abs(total_seconds)

        for breakdown_units in self.breakdowns:
            if not any(
                (unit := units.get_unit(unit_abbreviation)) is not None  # Check if unit is not None
                and Decimal(unit.value) >= self.precision
                for unit_abbreviation in breakdown_units
            ):
                continue

            breakdown_result = self._calculate_breakdown(total_seconds, breakdown_units, units)
            output.append(" ".join(breakdown_result))

        return "\n".join(f"{prefix}{line}" for line in output)


class AnchorManager:
    """A class to manage time anchors, allowing adding new anchors, sorting by
    value, and accessing them by abbreviation."""

    def __init__(self, units: UnitManager) -> None:
        """Create the AnchorManager object with Anchor objects inside."""
        self._anchors: Dict[str, Anchor] = {}
        self.units = units

    def add_anchor(self, anchor_config: AnchorConfig) -> None:
        """Adds a new anchor using the given configuration object.

        Args:
            anchor_config: AnchorConfig object containing the configuration for the new anchor.
        """
        decimal_anchor = anchor_config._replace(value=value_to_decimal(anchor_config.value))

        # Add the anchor to the dictionary
        self._anchors[anchor_config.label] = Anchor(decimal_anchor)

    def delete_anchor(self, label: str) -> None:
        """Deletes an anchor by its label.

        Args:
            label (str): The label of the anchor to delete.

        Raises:
            KeyError: If the label does not exist in the manager.
        """
        if label not in self._anchors:
            raise KeyError(f"Anchor with label '{label}' does not exist.")
        del self._anchors[label]

    def __iter__(self) -> Iterator[Anchor]:
        """Returns an iterator over the anchors.

        :return: An iterator of Anchor objects.
        """
        return iter(self._anchors.values())

    def __getitem__(self, index: Union[int, str]) -> Anchor:
        """Makes the class subscriptable by allowing access via index or label.

        :param index: The index or label of the item to retrieve.
        :return: An Anchor object.
        :raises KeyError: If the label is not found.
        :raises IndexError: If the index is out of range.
        """
        if isinstance(index, int):  # Index-based access
            try:
                return list(self._anchors.values())[index]
            except IndexError as exc:
                raise IndexError(f"Index {index} is out of range.") from exc

        else:  # Label-based access
            if index in self._anchors:
                return self._anchors[index]
            raise KeyError(f"Label '{index}' not found.")

    def __len__(self) -> int:
        """Returns the number of anchors in the manager.

        :return: The number of anchors.
        """
        return len(self._anchors)

    def get(self, label: str) -> Optional[Anchor]:
        """Retrieves the anchor with the specified label.

        Args:
            label (str): The label of the anchor to retrieve.

        Returns:
            Optional[Anchor]: The anchor with the given label, or None if no such anchor exists.
        """
        return self._anchors.get(label, None)

    def get_label(self, anchor: Anchor) -> str:
        """Returns the label associated with a given anchor.

        :param anchor: The Anchor instance.
        :return: The label corresponding to the anchor.
        :raises ValueError: If the anchor is not found in the manager.
        """
        for label, stored_anchor in self._anchors.items():
            if stored_anchor == anchor:
                return label
        raise ValueError("Anchor not found in the manager.")

    def get_anchors_by_group(self, group_name: str) -> List[Anchor]:
        """Retrieves a list of anchors that belong to the specified group.

        Args:
            group_name (str): The name of the group to filter anchors.

        Returns:
            List[Anchor]: A list of anchors belonging to the specified group.
        """
        return [anchor for anchor in self._anchors.values() if group_name in (anchor.groups or [])]

    def get_anchors_from_str(self, input_text: str) -> List[Anchor]:
        """Parses a comma-separated string and returns a sorted list of
        `Anchor` objects.

        This method splits the input string by commas, retrieves `Anchor` objects associated
        with each item, and adds them to a list. It also includes additional anchors based on
        groups associated with each item. The resulting list is sorted by the `value` attribute
        of the `Anchor` objects.

        Args:
            input_text (str): A comma-separated string of items, each representing
                               an anchor or group identifier.

        Returns:
            List[Anchor]: A sorted list of `Anchor` objects.

        Raises:
            ValueError: If any of the items in the input string cannot be resolved to
                        an `Anchor` object.

        Notes:
            - The method first retrieves anchors using the `get()` method, and then
              appends anchors retrieved by group using `get_anchors_by_group()`.
            - The sorting is done based on the `value` attribute of the `Anchor` objects.
        """
        anchor_list = []
        for item in input_text.split(","):
            anchor = self.get(item)
            if anchor:
                anchor_list.append(anchor)
            anchor_list.extend(self.get_anchors_by_group(item))
        anchor_list.sort(key=lambda anchor: anchor.value)
        return anchor_list

    def print(self, label: Optional[str] = None) -> None:
        """Prints details of all anchors inside the AnchorManager."""
        if label:
            # If a label is provided, print only the anchor with that label
            anchor = self._anchors.get(label)
            if anchor:
                anchor.print()
            else:
                print(f"Anchor with label '{label}' not found.")
        else:
            # If no label is provided, print all anchors
            for anchor in self._anchors.values():
                anchor.print()
