from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Optional

from utms.core.formats import TimeUncertainty
from utms.core.formats import registry as format_registry
from utms.core.mixins.model import ModelMixin
from utms.utils import ColorFormatter


@dataclass
class FormatSpec:
    """Specification for how to format an anchor's value."""

    units: Optional[List[str]] = None
    style: str = "default"
    format: Optional[str] = None
    options: dict = field(default_factory=dict)

    def __post_init__(self):
        # Only default to "UNITS" if no format was specified
        if self.units and not self.format:
            self.format = "UNITS"

        # Always ensure units are in options if present
        if self.units and "units" not in self.options:
            self.options["units"] = self.units


@dataclass
class Anchor(ModelMixin):
    """Represents a time anchor with its properties."""

    label: str
    name: str
    name_original: Optional[str]
    value: Decimal
    value_original: Optional[str]
    formats: List[FormatSpec] = field(default_factory=list)
    groups: List[str] = field(default_factory=list)
    uncertainty: Optional[TimeUncertainty] = None

    def __post_init__(self):
        # Ensure formats is never None
        if not self.formats:
            self.formats = [FormatSpec(format="CALENDAR")]

        # Ensure groups is never None
        if self.groups is None:
            self.groups = []

        # Set default uncertainty if none provided
        if self.uncertainty is None:
            self.uncertainty = TimeUncertainty(absolute=Decimal("1e-9"))

    def __repr__(self) -> str:
        return (
            f"Anchor(label={self.label}, name={self.name}, "
            f"value={self.value}, groups={self.groups})"
        )

    def __hash__(self):
        return hash(self.label)

    def __eq__(self, other):
        if not isinstance(other, Anchor):
            return False
        return self.label == other.label

    def format(self, total_seconds: Decimal, units: "FixedUnitManagerProtocol") -> str:
        """Format the anchor value using specified formats."""
        output = []
        self.logger.debug(
            "Processing formats: %s", self.formats
        )  # Note: changed from self._formats

        for format_spec in self.formats:
            self.logger.debug("Processing format spec: %s", format_spec)
            if format_spec.format:
                self.logger.debug(
                    "Using format: %s with options %s", format_spec.format, format_spec.options
                )
                result = format_registry.format(
                    format_spec.format, total_seconds, units, self.uncertainty, format_spec.options
                )
                output.append(result)
            elif format_spec.units:
                result = {}
                remaining = abs(total_seconds)
                self.logger.debug("Format spec units: %s", format_spec.units)
                if total_seconds > 0:
                    prefix = ColorFormatter.green("  + ")
                else:
                    prefix = ColorFormatter.red("  - ")

                for unit_label in format_spec.units:
                    unit = units.get_unit(unit_label)
                    self.logger.debug(
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
