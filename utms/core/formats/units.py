from dataclasses import dataclass
from decimal import Decimal
from enum import Enum, auto
from typing import Dict, List, Optional

from utms.utms_types import FixedUnitManagerProtocol

from ...utils import ColorFormatter
from utms.core.logger import get_logger
from utms.core.config import constants
from .base import FormatterProtocol, FormattingOptions, NotationType
from .config import TimeUncertainty

logger = get_logger()


def filter_relevant_units(total_seconds: Decimal, unit_list: List) -> List:
    """
    Filter units based on rough timestamp ranges and scientific meaningfulness.

    Args:
        total_seconds: The time difference in seconds
        unit_list: List of units sorted from largest to smallest

    Returns:
        Filtered list containing only meaningful units for this timeframe
    """
    abs_seconds = abs(total_seconds)
    YEAR = constants.SECONDS_IN_YEAR

    # Rough ranges and their meaningful smallest units
    TIME_RANGES = [
        # (range in seconds, smallest meaningful unit value)
        (Decimal(YEAR), Decimal("1e-9")),  # < 1 year: nano
        (Decimal(YEAR * 10), Decimal("1e-6")),  # < 10 years: micro
        (Decimal(YEAR * 100), Decimal("1")),  # < 100 years: seconds
        (Decimal(YEAR * 1000), Decimal("60")),  # < 1000 years: minutes
        (Decimal(YEAR * 10000), Decimal("3600")),  # < 10K years: hours
        (Decimal(YEAR * 100000), Decimal("86400")),  # < 100K years: days
        (Decimal(YEAR * 1000000), Decimal("2592000")),  # < 1M years: months
        (Decimal(YEAR * 10000000), Decimal("31556925")),  # < 10M years: years
    ]

    # Find appropriate minimum unit value
    min_unit_value = Decimal("1e-9")  # default to microseconds
    for range_seconds, min_value in TIME_RANGES:
        if abs_seconds < range_seconds:
            break
        min_unit_value = min_value

    logger.debug(f"Time value: {abs_seconds} seconds")
    logger.debug(f"Selected minimum unit value: {min_unit_value}")

    # Filter units
    relevant_units = [unit for unit in unit_list if Decimal(unit.value) >= min_unit_value]

    logger.debug(f"Filtered units: {[u.label for u in relevant_units]}")
    return relevant_units


class UnitsFormatter(FormatterProtocol):
    def format(
        self,
        total_seconds: Decimal,
        units: FixedUnitManagerProtocol,
        uncertainty: TimeUncertainty,
        options: dict,
    ) -> str:
        opts = FormattingOptions(**options)
        # Get the units to use
        if opts.units:
            # Use specifically requested units
            unit_list = [units.get(u) for u in opts.units]
        else:
            # Use automatically determined units
            unit_list = self._get_meaningful_units(total_seconds, uncertainty, units)

        if not unit_list:
            return "No appropriate unit found"

        # Calculate values for each unit
        result = self._calculate_unit_values(total_seconds, unit_list)

        # Format the result
        formatted = self._format_result(total_seconds, result, units, uncertainty, opts)
        return self._add_prefix(formatted, total_seconds, opts.raw)

    def _calculate_unit_values(self, total_seconds: Decimal, unit_list: List) -> Dict[str, Decimal]:
        result = {}
        remaining = abs(total_seconds)

        for i, unit in enumerate(unit_list):
            unit_value = Decimal(unit.value)

            # For the last unit, include decimal places
            if i == len(unit_list) - 1:
                count = remaining / unit_value
            else:
                count = remaining // unit_value
                remaining %= unit_value

            result[unit.label] = count

        return result

    def _format_result(
        self,
        total_seconds: Decimal,
        result: Dict[str, Decimal],
        units: FixedUnitManagerProtocol,
        uncertainty: TimeUncertainty,
        opts: FormattingOptions,
    ) -> str:
        if opts.notation != NotationType.STANDARD:
            return self._format_scientific(total_seconds, uncertainty, opts)

        return self._format_units(result, units, opts)

    def _format_units(
        self, result: Dict[str, Decimal], units: FixedUnitManagerProtocol, opts: FormattingOptions
    ) -> str:
        parts = []
        style = opts.style
        started = False

        for unit_label, count in result.items():
            # Skip leading zeros
            if not started and count == 0:
                continue

            # Mark that we've found our first non-zero value
            started = True

            # Format the count
            if isinstance(count, Decimal) and count % 1 != 0:
                value_str = f"{count:.2f}"
            else:
                value_str = f"{int(count)}"

            if style == "full":
                unit_name = units.get(unit_label).name + ("s" if count != 1 else "")
                unit_str = unit_name if opts.raw else ColorFormatter.green(unit_name)
                parts.append(f"{value_str} {unit_str}")
            elif style == "short":
                unit_str = unit_label if opts.raw else ColorFormatter.green(unit_label)
                parts.append(f"{value_str}{unit_str}")
            elif style == "compact":
                unit_str = unit_label if opts.raw else ColorFormatter.green(unit_label)
                parts.append(f"{value_str}{unit_str}")

        if not parts:  # If all values were zero
            unit = units.get(next(iter(result)))  # Get first unit
            if style == "full":
                unit_str = unit.name if opts.raw else ColorFormatter.green(unit.name)
                return f"0 {unit_str}s"
            else:
                unit_str = unit.label if opts.raw else ColorFormatter.green(unit.label)
                return f"0{unit_str}"

        if style == "compact":
            return "".join(parts)
        elif style == "full":
            return ", ".join(parts)
        else:  # short
            return " ".join(parts)

    def _get_meaningful_units(
        self, total_seconds: Decimal, uncertainty: TimeUncertainty, units: FixedUnitManagerProtocol
    ) -> List:
        decimal_units = sorted(
            units.get_units_by_groups(["decimal", "scientific", "second"], True),
            key=lambda u: Decimal(u.value),
            reverse=True,
        )

        relevant_units = filter_relevant_units(total_seconds, decimal_units)
        meaningful_units = []
        remaining = abs(total_seconds)

        for unit in relevant_units:
            unit_value = Decimal(unit.value)

            # Calculate both uncertainties at this scale
            abs_uncertainty = uncertainty.absolute
            rel_uncertainty = uncertainty.relative * unit_value

            # Use the larger uncertainty at this scale
            effective_uncertainty = max(abs_uncertainty, rel_uncertainty)

            logger.debug(
                f"Unit {unit.label}: value={unit_value}, "
                f"abs_unc={abs_uncertainty}, rel_unc={rel_uncertainty}, "
                f"effective_unc={effective_uncertainty}"
            )

            # Skip if uncertainty is larger than unit value
            if effective_uncertainty >= unit_value:
                break

            # Calculate how many of this unit we have
            count = remaining // unit_value

            # Only include units with non-zero values
            if count > 0:
                meaningful_units.append(unit)
                remaining %= unit_value
                logger.debug(f"Added unit {unit.label} (count={count}, remaining={remaining})")

        # Always include at least one unit
        if not meaningful_units and relevant_units:
            meaningful_units.append(relevant_units[-1])

        return meaningful_units

    def _add_prefix(self, formatted: str, value: Decimal, raw: bool) -> str:
        if raw:
            return ("+" if value > 0 else "-") + formatted
        return (
            ColorFormatter.green("  + ") if value > 0 else ColorFormatter.red("  - ")
        ) + formatted
