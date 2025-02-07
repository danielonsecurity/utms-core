from decimal import Decimal
from dataclasses import dataclass

from utms.utms_types import FixedUnitManagerProtocol
from ...utils import ColorFormatter, get_logger
from .base import FormatterProtocol

from typing import Optional, List, Dict

from .config import FormatterConfig, TimeUncertainty

from enum import Enum, auto
from decimal import Decimal

from .base import FormattingOptions, NotationType

logger = get_logger("core.formats.scientific")


class ScientificFormatter(FormatterProtocol):
    def __init__(self, config: Optional[FormatterConfig] = None):
        self.config = config or FormatterConfig()

    def format(self, total_seconds: Decimal, units: FixedUnitManagerProtocol, 
               uncertainty: TimeUncertainty, options: dict) -> str:
        opts = FormattingOptions(**options)
        unit_list = options.get("units", ["s"])
        if not unit_list:
            unit_list = ["s"]
        # Sort units by size (largest to smallest)
        units_info = [units.get_unit(u) for u in unit_list]
        units_info.sort(key=lambda u: Decimal(u.value), reverse=True)
        
        result = []
        remaining = abs(total_seconds)
        
        # Process all units except the last one
        for unit in units_info[:-1]:
            unit_value = Decimal(unit.value)
            count = remaining // unit_value
            if count > 0:
                remaining %= unit_value
                unit_text = unit.abbreviation if opts.abbreviated else unit.name
                if opts.plural:
                    unit_text += "s"
                if not opts.raw:
                    unit_text = ColorFormatter.green(unit_text)
                space = "" if opts.compact else " "
                result.append(f"{int(count)}{space}{unit_text}")
        
        # Handle the smallest unit in scientific notation
        if remaining > 0 and units_info:
            smallest_unit = units_info[-1]
            unit_text = smallest_unit.abbreviation if opts.abbreviated else smallest_unit.name
            if opts.plural:
                unit_text += "s"
            if not opts.raw:
                unit_text = ColorFormatter.green(unit_text)
            space = "" if opts.compact else " "
            formatted_number = self._format_number(remaining, uncertainty, opts)
            result.append(f"{formatted_number}{space}{unit_text}")
        
        formatted = opts.separator.join(result)
        return self._add_prefix(formatted, total_seconds, opts)

    def _format_number(self, value: Decimal, uncertainty: TimeUncertainty, opts: FormattingOptions) -> str:
        """Format a number according to the specified notation."""
        abs_value = abs(value)
        if opts.notation == NotationType.STANDARD:
            return f"{abs_value:.2f}"

        elif opts.notation == NotationType.SCIENTIFIC:
            return f"{abs_value:.3e}"  # 1.739e9

        elif opts.notation == NotationType.ENGINEERING:
            # Convert to engineering notation (powers of 3)
            exp = abs_value.adjusted()
            eng_exp = (exp // 3) * 3
            mantissa = abs_value / Decimal(10) ** eng_exp
            return f"{mantissa:.3f}×10{self._superscript(eng_exp)}"  # 1.739×10⁹



        elif opts.notation == NotationType.MEASUREMENT:
            exp = abs_value.adjusted()
            eng_exp = (exp // 3) * 3
            mantissa = abs_value / Decimal(10) ** eng_exp
            if opts.show_uncertainty:
                uncert = uncertainty.get_effective_uncertainty(value)
                uncert_mantissa = uncert / Decimal(10) ** eng_exp
                logger.debug("Value: %s", value)
                logger.debug("Effective uncertainty: %s", uncert)
                logger.debug("Scaled uncertainty mantissa: %s", uncert_mantissa)
                logger.debug("Mantissa: %s", mantissa)
                logger.debug("eng_exp: %s", eng_exp)

                # Calculate decimal places based on relative magnitude
                if uncert_mantissa > 0:
                    decimal_places = -uncert_mantissa.adjusted()
                    uncertainty_digits = int(round(uncert_mantissa * Decimal(10) ** decimal_places))

                logger.debug(f"Decimal places: {decimal_places}")
                logger.debug(f"Uncertainty digits: {uncertainty_digits}")

                return f"{mantissa:.{decimal_places}f}({uncertainty_digits})×10{self._superscript(eng_exp)}"

        return f"{abs_value:.3e}"  # fallback to scientific



    def _superscript(self, n: int) -> str:
        """Convert number to superscript."""
        superscript_map = str.maketrans("0123456789+-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻")
        return str(n).translate(superscript_map)



    def _add_prefix(self, formatted: str, value: Decimal, opts: dict) -> str:
        prefix = ""
        if opts.indented:
            padding = "  "
        else:
            padding = ""
        prefix += padding

        sign = "+" if value > 0 else "-"
        if not opts.raw:
            sign = ColorFormatter.green(sign) if value > 0 else ColorFormatter.red(sign)

        if opts.signed:
            prefix += sign

        if not opts.compact:
            prefix += " "

        return prefix + formatted
