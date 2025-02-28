from dataclasses import dataclass
from decimal import Decimal
from enum import Enum, auto
from typing import Dict, List, Optional

from utms.utils import color_scientific_format
from utms.utms_types import FixedUnitManagerProtocol

from ...utils import ColorFormatter, get_logger
from .base import FormatterProtocol, FormattingOptions, NotationType
from .config import TimeUncertainty

logger = get_logger("core.formats.scientific")


class ScientificFormatter(FormatterProtocol):
    def format(
        self,
        total_seconds: Decimal,
        units: FixedUnitManagerProtocol,
        uncertainty: TimeUncertainty,
        options: dict,
    ) -> str:
        opts = FormattingOptions(**options)
        unit_list = options.get("units", ["s"])
        if not unit_list:
            unit_list = ["s"]
        # Sort units by size (largest to smallest)
        units_info = [units.get(u) for u in unit_list]
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
            formatted_number = self._format_number(total_seconds, remaining, uncertainty, opts)
            result.append(f"{formatted_number}{space}{unit_text}")

        separator = opts.separator
        if not opts.raw:
            separator = ColorFormatter.yellow(separator)
        formatted = separator.join(result)
        return self._add_prefix(formatted, total_seconds, opts)

    def _format_number(
        self,
        total_seconds: Decimal,
        value: Decimal,
        uncertainty: TimeUncertainty,
        opts: FormattingOptions,
    ) -> str:
        """Format a number according to the specified notation."""
        abs_value = abs(value)
        uncert = uncertainty.get_effective_uncertainty(total_seconds)
        significant_digits = opts.significant_digits
        if opts.notation == NotationType.STANDARD:
            if opts.show_uncertainty:
                separator = "±" if opts.compact else " ± "
                uncert_str = f"{uncert:.{significant_digits}e}"
                if not opts.raw:
                    separator = ColorFormatter.red(separator)
                    uncert_str = color_scientific_format(uncert_str)
                return f"{abs_value:.{significant_digits}f}{separator}{uncert_str}"
            return f"{abs_value:.{significant_digits}f}"

        elif opts.notation == NotationType.SCIENTIFIC:
            abs_value_str = f"{abs_value:.{significant_digits}e}"
            if opts.show_uncertainty:
                separator = "±" if opts.compact else " ± "
                uncert_str = f"{uncert:.{significant_digits}e}"
                if not opts.raw:
                    separator = ColorFormatter.red(separator)
                    abs_value_str = color_scientific_format(abs_value_str)
                    uncert_str = color_scientific_format(uncert_str)
                return abs_value_str + separator + uncert_str
            if not opts.raw:
                abs_value_str = color_scientific_format(abs_value_str)
            return abs_value_str

        elif opts.notation == NotationType.ENGINEERING:
            exp = abs_value.adjusted()
            eng_exp = (exp // 3) * 3
            mantissa = abs_value / Decimal(10) ** eng_exp
            mantissa_str = f"{mantissa:.{significant_digits}f}"
            if opts.show_uncertainty:
                separator = "±" if opts.compact else " ± "
                uncert_str = f"{uncert:.{significant_digits}e}"
                if not opts.raw:
                    separator = ColorFormatter.red(separator)
                    uncert_str = color_scientific_format(uncert_str)
                result = mantissa_str
                result += "×" if opts.raw else ColorFormatter.red("×")
                result += "10"
                result += self._superscript(eng_exp)
                result += separator
                result += uncert_str

                return result
            result = mantissa_str
            result += "×" if opts.raw else ColorFormatter.red("×")
            result += "10"
            result += self._superscript(eng_exp)
            return result

        elif opts.notation == NotationType.MEASUREMENT:
            # Get effective uncertainty
            uncert = uncertainty.get_effective_uncertainty(total_seconds)

            # Convert to engineering notation (powers of 3)
            exp = abs_value.adjusted()
            eng_exp = (exp // 3) * 3
            mantissa = abs_value / Decimal(10) ** eng_exp
            uncert_mantissa = uncert / Decimal(10) ** eng_exp

            # Calculate significant figures based on uncertainty
            if uncert_mantissa > 0:
                if opts.significant_digits:
                    sig_figs = opts.significant_digits
                else:
                    sig_figs = -uncert_mantissa.adjusted()
                    if sig_figs < 0:
                        sig_figs = 0

                # Format the uncertainty digits
                uncert_scaled = uncert_mantissa * Decimal(10) ** sig_figs
                uncert_digits = int(round(uncert_scaled))

                # Format the mantissa with correct precision
                mantissa_str = f"{mantissa:.{sig_figs}f}"

                logger.debug(f"Value: {abs_value}")
                logger.debug(f"Uncertainty: {uncert}")
                logger.debug(f"Engineering exponent: {eng_exp}")
                logger.debug(f"Mantissa: {mantissa}")
                logger.debug(f"Uncertainty mantissa: {uncert_mantissa}")
                logger.debug(f"Significant figures: {sig_figs}")
                logger.debug(f"Uncertainty digits: {uncert_digits}")

                result = f"{mantissa_str}"
                if not opts.raw:
                    result += ColorFormatter.magenta("(")
                else:
                    result += "("

                result += str(uncert_digits)
                if not opts.raw:
                    result += ColorFormatter.magenta(")")
                else:
                    result += ")"

                result += "×" if opts.raw else ColorFormatter.red("×")
                result += f"10{self._superscript(eng_exp)}"
                if opts.show_uncertainty:
                    uncert = uncertainty.get_effective_uncertainty(total_seconds)
                    separator = "±" if opts.compact else " ± "
                    if not opts.raw:
                        separator = ColorFormatter.red(separator)
                    result += separator
                    uncert_str = f"{uncert:.{sig_figs}e}"
                    if not opts.raw:
                        uncert_str = color_scientific_format(uncert_str)
                    result += uncert_str

                if opts.show_confidence:
                    low, high = uncertainty.get_confidence_interval(abs_value)
                    low_mantissa = low / Decimal(10) ** eng_exp
                    high_mantissa = high / Decimal(10) ** eng_exp
                    ci_format = " "
                    ci_format += "[" if opts.raw else ColorFormatter.magenta("[")
                    ci_format += "95% CI: "
                    ci_format += f"{low_mantissa:.{sig_figs}f}"
                    ci_format += "-" if opts.raw else ColorFormatter.red("-")
                    ci_format += f"{high_mantissa:.{sig_figs}f}"
                    ci_format += "×" if opts.raw else ColorFormatter.red("×")
                    ci_format += "10"
                    ci_format += self._superscript(eng_exp)
                    ci_format += "]" if opts.raw else ColorFormatter.magenta("]")
                    result += ci_format

                return result

            # Fallback if uncertainty is 0
            return f"{mantissa:.3f}×10{self._superscript(eng_exp)}"

        return f"{abs_value:.3e}"  # fallback

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
