from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol

from ...utils import ColorFormatter
from ...utms_types import FixedUnitManagerProtocol
from .config import TimeUncertainty


class FormatterProtocol(Protocol):
    """Base protocol for all formatters."""

    def format(
        self,
        total_seconds: Decimal,
        units: FixedUnitManagerProtocol,
        uncertainty: TimeUncertainty,
        options: Optional[Dict[str, Any]],
    ) -> str:
        """Format total_seconds using the given units."""
        ...


class NotationType(Enum):
    STANDARD = "standard"
    SCIENTIFIC = "scientific"  # 1.74e+9
    ENGINEERING = "engineering"  # 1.74×10⁹
    MEASUREMENT = "measurement"  # 1.738809452(174)×10⁹


@dataclass
class FormattingOptions:
    style: str = "full"
    abbreviated: bool = False
    raw: bool = False
    show_uncertainty: bool = False
    show_confidence: bool = False
    signed: bool = True
    compact: bool = False
    separator: str = " + "
    plural: bool = True
    indented: bool = True
    significant_digits: int = 3
    notation: NotationType = NotationType.STANDARD
    units: Optional[List[str]] = None
    currency: str = "€"
    position_right: bool = True
    base_unit: str = "h"
    rate: Decimal = Decimal(0)
    show_rate: bool = False
    format_string: str = "%Y-%M-%dT%h:%m:%s"

    def __post_init__(self):
        if isinstance(self.notation, str):
            self.notation = NotationType(self.notation)
        # Convert units to list if it's a single string
        if isinstance(self.units, str):
            self.units = [self.units]
        # Ensure units is always a list or None
        elif self.units is not None and not isinstance(self.units, list):
            self.units = list(self.units)

        # Convert string booleans
        for attr in [
            "abbreviated",
            "raw",
            "signed",
            "compact",
            "show_uncertainty",
            "show_confidence",
            "plural",
            "indented",
        ]:
            value = getattr(self, attr)
            if isinstance(value, str):
                setattr(self, attr, value.lower() == "true")


class DateTimeFormatterBase(FormatterProtocol):
    def _format_with_style(
        self,
        result: Dict[str, int],
        unit_labels: Dict[str, str],
        total_seconds: Decimal,
        style: str,
        raw: bool,
    ) -> str:
        """Common formatting logic for calendar/clock formatters."""
        # Filter out zero values
        non_zero_results = {unit: count for unit, count in result.items() if count > 0}

        # If all values are zero, show zero with the smallest unit
        if not non_zero_results and result:
            smallest_unit = list(result.keys())[-1]
            non_zero_results = {smallest_unit: 0}

        if style == "full":
            if raw:
                prefix = "+" if total_seconds > 0 else "-"
                parts = [
                    f"{count:02d} {unit_labels[unit]}" for unit, count in non_zero_results.items()
                ]
                return f"{prefix}{', '.join(parts)}"
            else:
                prefix = (
                    ColorFormatter.green("  + ")
                    if total_seconds > 0
                    else ColorFormatter.red("  - ")
                )
                parts = [
                    f"{count:02d} {ColorFormatter.green(unit_labels[unit])}"
                    for unit, count in non_zero_results.items()
                ]
                return f"{prefix}{', '.join(parts)}"

        elif style == "short":
            if raw:
                formatted = " ".join(
                    f"{count:02d} '{unit}'" for unit, count in non_zero_results.items()
                )
                prefix = "+" if total_seconds > 0 else "-"
                return prefix + formatted
            else:
                formatted = " ".join(
                    f"{count:02d} {ColorFormatter.green(unit)}"
                    for unit, count in non_zero_results.items()
                )
                prefix = (
                    ColorFormatter.green("  + ")
                    if total_seconds > 0
                    else ColorFormatter.red("  - ")
                )
                return prefix + formatted

        elif style == "compact":
            if raw:
                formatted = "".join(
                    f"{count:02d}{unit}" for unit, count in non_zero_results.items()
                )
                prefix = "+" if total_seconds > 0 else "-"
                return prefix + formatted
            else:
                formatted = "".join(
                    f"{count:02d}{ColorFormatter.green(unit)}"
                    for unit, count in non_zero_results.items()
                )
                prefix = (
                    ColorFormatter.green("  + ")
                    if total_seconds > 0
                    else ColorFormatter.red("  - ")
                )
                return prefix + formatted
