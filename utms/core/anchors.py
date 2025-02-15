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

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Iterator, List, Optional, Union

import hy
from colorama import Fore, Style
from proto import utils

from ..resolvers import HyAST, HyNode
from ..utils import (
    ColorFormatter,
    get_logger,
    hy_to_python,
    list_to_dict,
    python_to_hy,
    value_to_decimal,
)
from ..utms_types import (
    AnchorConfigProtocol,
    AnchorManagerProtocol,
    AnchorProtocol,
    FixedUnitManagerProtocol,
    HyProperty,
    is_list,
    is_string,
)
from . import constants
from .formats import TimeUncertainty
from .formats import registry as format_registry

# from .units import FixedUnitManager

logger = get_logger("core.anchors")


def evaluate_with_variables(expr, variables):
    """Evaluate expression with variables, returning original if evaluation fails."""
    try:
        if isinstance(expr, (hy.models.Expression, hy.models.Symbol)):
            return hy.eval(expr, locals=variables)
        return expr
    except Exception as e:
        logger.debug(f"Could not evaluate {expr}: {e}")
        return expr


class AnchorConfig(AnchorConfigProtocol):
    """Implementation of AnchorConfigProtocol."""

    def __init__(
        self,
        label: str,
        name: str,
        value: Union[Decimal, datetime],
        formats: Optional[List[str]] = ["CALENDAR"],
        groups: Optional[List[str]] = None,
        uncertainty: Optional[TimeUncertainty] = None,
    ) -> None:
        self.label = label
        self._properties = {}

        # Store all properties with their original expressions

        for key, item_value in locals().items():
            if key in ["self", "label", "_properties"]:
                continue
            if isinstance(value, (hy.models.Expression, hy.models.Symbol)):
                self._properties[key] = HyProperty(
                    value=evaluate_with_variables(item_value, {}), original=hy.repr(item_value)
                )
            else:
                self._properties[key] = HyProperty(value=item_value)

        self.name = name
        self.value = value
        self.groups = groups
        self.formats = formats
        if uncertainty:
            uncertainty = list_to_dict(hy_to_python(uncertainty))
            self.uncertainty = TimeUncertainty(
                absolute=uncertainty.get("absolute", Decimal("1e-9")),
                relative=uncertainty.get("relative", Decimal("1e-9")),
                confidence_95=uncertainty.get("confidence_95", None),
            )
        else:
            self.uncertainty = TimeUncertainty(absolute=Decimal("1e-9"))

    def get_value(self, key: str) -> Any:
        """Get the evaluated value of a property."""
        prop = self._properties.get(key)
        return prop.value if prop else None

    def get_original(self, key: str) -> Optional[Any]:
        """Get the original expression of a property."""
        prop = self._properties.get(key)
        return prop.original if prop else None


@dataclass
class FormatSpec:
    units: Optional[List[str]] = None  # For unit-based formats like ["Y", "d"]
    style: str = "default"  # Style for unit-based formats
    format: Optional[str] = None  # For predefined formats like "CALENDAR"
    options: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Only default to "UNITS" if no format was specified
        if self.units and not self.format:
            self.format = "UNITS"

        # Always ensure units are in options if present
        if self.units and "units" not in self.options:
            self.options["units"] = self.units

    def to_hy(self) -> Any:
        """Convert FormatSpec to Hy-compatible format."""
        if hasattr(self, "original_expr"):
            return self.original_expr

        if self.format and not self.units:
            return self.format

        if self.units and not self.options:
            return self.units

        result = {}
        if self.format:
            result["format"] = self.format
        if self.units:
            result["units"] = self.units
        if self.options:
            cleaned_options = {
                k: v for k, v in self.options.items() if k != "units" or v != self.units
            }
            if cleaned_options:
                result["options"] = cleaned_options
        return result


class Anchor(AnchorProtocol):
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
        breakdown(total_seconds: Decimal, units: FixedUnitManager) -> str:
            Breaks down a given total duration (in seconds) into the configured units and returns a
            formatted string representing the breakdown.

        _apply_color(value: str, color: str = Fore.BLUE) -> str:
            Applies the specified color style to the given value.

        _format_breakdown_entry(count: Union[int, Decimal], unit: str) -> str:
            Formats a single breakdown entry, ensuring proper string formatting and color styling.

        _calculate_breakdown(total_seconds: Decimal, breakdown_units: List[str], units: FixedUnitManager)
        -> List[str]:
            Calculates the breakdown for a given set of units based on the total duration and
            precision.
    """

    def __init__(self, anchor_config: AnchorConfig) -> None:
        """Create the Anchor object with its parameters inside."""
        self._label = anchor_config.label
        logger.debug("Initializing anchor %s", self._label)
        self._name = anchor_config.name
        self._properties = anchor_config._properties
        self._value = value_to_decimal(anchor_config.value)
        self._uncertainty = anchor_config.uncertainty
        self._formats = []
        self._groups = anchor_config.groups or []
        # Handle formats
        if not anchor_config.formats:
            self._formats.append(FormatSpec(format="CALENDAR"))
            logger.debug("No formats specified, using default CALENDAR format")
        else:
            for format_spec in anchor_config.formats or []:
                logger.debug("Processing format_spec: %s", format_spec)
                py_format_spec = list_to_dict(hy_to_python(format_spec))
                logger.debug("Converted to: %s", py_format_spec)
                if is_string(format_spec):
                    logger.debug("Processing as string")
                    self._formats.append(FormatSpec(format=hy_to_python(format_spec)))
                elif is_list(format_spec):
                    units = [hy_to_python(u) for u in format_spec]
                    self._formats.append(
                        FormatSpec(
                            format="UNITS",
                            units=units,
                            style="full",
                            options=py_format_spec.get("options", {}),
                        )
                    )
                elif isinstance(format_spec, (dict, hy.models.Dict)):
                    py_format_spec = list_to_dict(hy_to_python(format_spec))
                    format_name = py_format_spec.get("format")

                    if "units" in py_format_spec:
                        logger.debug("Processing format with units")
                        units = py_format_spec["units"]
                        if isinstance(units[0], list):
                            units = units[0]
                        logger.debug("Final units: %s", units)
                        options = py_format_spec.get("options", {})
                        if isinstance(options, list):
                            options = list_to_dict(options)

                        # Use specified format or default to "UNITS"
                        self._formats.append(
                            FormatSpec(
                                format=format_name or "UNITS",  # Use specified format
                                units=units,
                                style=py_format_spec.get("style", "full"),
                                options=options,
                            )
                        )

                    elif format_name:  # If format is specified without units
                        logger.debug("Processing as format")
                        options = {}
                        if "options" in py_format_spec:
                            options = list_to_dict(py_format_spec["options"])
                        logger.debug("Format name: %s, options: %s", format_name, options)
                        self._formats.append(
                            FormatSpec(
                                format=format_name,
                                options=options,
                            )
                        )
                        logger.debug("Created format spec: %s", self._formats[-1])

            logger.debug("Initializing anchor %s", self._label)

    # Read-only properties
    @property
    def label(self) -> str:
        return self._label

    @property
    def name(self) -> str:
        return self._name

    @property
    def value(self) -> Decimal:
        return self._value

    @property
    def formats(self) -> List[List[str]]:
        return self._formats

    @property
    def groups(self) -> List[str]:
        return self._groups

    @property
    def uncertainty(self) -> Decimal:
        return self._uncertainty

    def format(self, total_seconds: Decimal, units: "FixedUnitManagerProtocol") -> str:
        output = []
        logger.debug("Processing formats: %s", self._formats)

        for format_spec in self._formats:
            logger.debug("Processing format spec: %s", format_spec)
            if format_spec.format:
                logger.debug(
                    "Using format: %s with options %s", format_spec.format, format_spec.options
                )
                result = format_registry.format(
                    format_spec.format, total_seconds, units, self.uncertainty, format_spec.options
                )
                output.append(result)
            elif format_spec.units:
                result = {}
                remaining = abs(total_seconds)
                logger.debug("Format spec units: %s", format_spec.units)
                if total_seconds > 0:
                    prefix = ColorFormatter.green("  + ")
                else:
                    prefix = ColorFormatter.red("  - ")

                for unit_label in format_spec.units:
                    unit = units.get_unit(unit_label)
                    logger.debug(
                        "Processing unit_label: %s, type: %s", unit_label, type(unit_label)
                    )
                    if not unit:
                        continue

                    unit_value = Decimal(unit.value)
                    if unit_label == format_spec.units[-1]:
                        count = remaining / unit_value
                    else:
                        count = remaining // unit_value
                        remaining %= unit_value
                    result[unit_label] = count

                # Format according to style
                if format_spec.style == "default":
                    parts = []
                    for i, unit in enumerate(format_spec.units):
                        unit_info = units.get_unit(unit)
                        value = result[unit]

                        # Only last unit gets decimal places
                        if i == len(format_spec.units) - 1:
                            formatted_value = f"{value:.2f}"
                        else:
                            formatted_value = f"{int(value)}"

                        parts.append(
                            f"{formatted_value} {ColorFormatter.green(unit_info.name + 's')}"
                        )

                    formatted = prefix + ", ".join(parts)
                    output.append(formatted)
        return "\n".join(output)

    def display(self, total_seconds: Decimal, units: "FixedUnitManagerProtocol") -> str:
        """Combines both breakdown and format outputs"""
        parts = []

        # Add traditional breakdowns
        breakdown_result = self.breakdown(total_seconds, units)
        if breakdown_result:
            parts.append(breakdown_result)

        # Add new format outputs
        format_result = self.format(total_seconds, units)
        if format_result:
            parts.append(format_result)

        return "\n".join(parts)

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
        self, total_seconds: Decimal, breakdown_units: List[str], units: "FixedUnitManagerProtocol"
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
        print(f"{apply_green_color('Formats')}:")
        for format in self.formats:
            print(f"  - {format}")
        print("-" * 50)

    def breakdown(self, total_seconds: Decimal, units: "FixedUnitManagerProtocol") -> str:
        """Breaks down a duration in seconds into multiple unit formats.

        Args:
            total_seconds (Decimal): Total duration in seconds.
            units (UnitManager): FixedUnitManager instance for unit details.

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
                units.get_unit(unit_abbreviation) is not None  # Check if unit is not None
                for unit_abbreviation in breakdown_units
            ):
                continue

            breakdown_result = self._calculate_breakdown(total_seconds, breakdown_units, units)
            output.append(" ".join(breakdown_result))

        return "\n".join(f"{prefix}{line}" for line in output)

    def to_hy(self) -> HyNode:
        """Convert anchor to AST node."""
        properties = []

        # Convert each property to a node
        for key, prop in self._properties.items():
            if prop.value is not None:
                if key in ['name', 'value']:  # Only debug fields we care about
                    print(f"\nProcessing anchor property: {key}")
                    print(f"Value: {prop.value}")
                    print(f"Type: {type(prop.value)}")

                # print(f"Key: {key}")
                # print(f"Property value: {prop.value}")
                # print(f"Property original: {prop.original}")
                if (
                    isinstance(prop.value, (hy.models.Expression, hy.models.Symbol))
                    or prop.original
                ):
                    value = prop.original or prop.value
                else:
                    value = prop.value

                properties.append(
                    HyNode(
                        type="property",
                        value=key,
                        children=[
                            HyNode(
                                type="value",
                                value=value,
                                original=prop.original,
                                is_dynamic=bool(prop.original),
                            )
                        ],
                    )
                )

        return HyNode(type="def-anchor", value=self._label, children=properties)



class AnchorManager(AnchorManagerProtocol):
    """A class to manage time anchors, allowing adding new anchors, sorting by
    value, and accessing them by abbreviation."""

    def __init__(self, units: FixedUnitManagerProtocol) -> None:
        """Create the AnchorManager object with Anchor objects inside."""
        self._anchors: Dict[str, Anchor] = {}
        self._units = units

    @property
    def units(self) -> FixedUnitManagerProtocol:
        return self._units

    def add_anchor(self, anchor: Anchor) -> None:
        self._anchors[anchor._label] = anchor

    def create_anchor(self, anchor_config: Anchor) -> None:
        """Adds a new anchor using the given configuration object.

        Args:
            anchor_config: AnchorConfig object containing the configuration for the new anchor.
        """
        decimal_value = value_to_decimal(anchor_config.value)
        self._anchors[anchor_config.label] = Anchor(
            AnchorConfig(
                label=anchor_config.label,
                name=anchor_config.name,
                value=decimal_value,
                # breakdowns=anchor_config.breakdowns,
                formats=anchor_config.formats,
                groups=anchor_config.groups,
            )
        )

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
        return [anchor for anchor in self._anchors.values() if group_name in (hy_to_python(anchor.groups) or [])]

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

    def save(self, filename: str) -> None:
        """Save all anchors to a Hy file."""
        ast_manager = HyAST()
        nodes = [
            anchor.to_hy() for anchor in sorted(self._anchors.values(), key=lambda a: a._value)
        ]
        # Write to file
        with open(filename, "w") as f:
            f.write(ast_manager.to_hy(nodes))
