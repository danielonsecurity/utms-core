from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, Optional

from utms.core.formats.base import FormattingOptions
from utms.utms_types import FixedUnitManagerProtocol

from ...utils import ColorFormatter
from .base import FormatterProtocol
from .config import TimeUncertainty


class CustomFormatter(FormatterProtocol):
    def format(
        self,
        total_seconds: Decimal,
        units: FixedUnitManagerProtocol,
        uncertainty: TimeUncertainty,
        options: dict,
    ) -> str:
        opts = FormattingOptions(**options)
        format_string = opts.format_string
        raw = opts.raw
        signed = opts.signed

        # Extract unit abbreviations from format string
        format_units = []
        for i, char in enumerate(format_string):
            if char == "%" and i + 1 < len(format_string):
                unit_abbrev = format_string[i + 1]
                format_units.append(unit_abbrev)

        # Get unit info and sort by value
        unit_info = []
        for abbrev in format_units:
            unit = units.get_unit(abbrev)
            if unit:
                unit_info.append(unit)
        unit_info.sort(key=lambda u: Decimal(u.value), reverse=True)

        # Calculate values for each unit
        remaining = abs(total_seconds)
        values = {}

        for unit in unit_info:
            unit_value = Decimal(unit.value)
            count = remaining // unit_value
            remaining %= unit_value
            values[f"%{unit.abbreviation}"] = int(count)

        # Replace each unit placeholder with its value
        result = format_string
        for unit_key, value in values.items():
            # Add leading zero for single-digit values
            if unit_key in ["%M", "%d", "%h", "%m", "%s"]:  # units that typically use leading zeros
                value_str = f"{value:02d}"
            else:
                value_str = f"{value}"

            if not raw:
                value_str = ColorFormatter.green(value_str)
            result = result.replace(unit_key, value_str)

        prefix = ""
        if opts.indented:
            prefix = "  "

        if signed:
            if total_seconds < 0:
                sign = "-" if raw else ColorFormatter.red("-")
            else:
                sign = "+" if raw else ColorFormatter.green("+")
            if not opts.compact:
                sign += " "
            prefix += sign
        # Add indentation if not raw
        # if not opts.raw:
        #     prefix += " "

        return prefix + result

        # # Add sign and color if needed
        # if not raw:
        #     if total_seconds < 0:
        #         return ColorFormatter.red(f"  - {result}")
        #     else:
        #         return ColorFormatter.green(f"  + {result}")
        # else:
        #     return ("-" if total_seconds < 0 else "+") + result
