from decimal import Decimal
from dataclasses import dataclass
from .. import constants

from utms.utms_types import FixedUnitManagerProtocol
from ...utils import ColorFormatter, get_logger
from .base import FormatterProtocol

from typing import Optional, List, Dict

from .config import FormatterConfig, TimeUncertainty

from enum import Enum, auto
from decimal import Decimal
from .base import FormattingOptions, NotationType

logger = get_logger("core.formats.units")

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
        (Decimal(YEAR),        Decimal('1e-9')),     # < 1 year: nano
        (Decimal(YEAR * 10),       Decimal('1e-6')),     # < 10 years: micro
        (Decimal(YEAR * 100),      Decimal('1')),        # < 100 years: seconds
        (Decimal(YEAR * 1000),     Decimal('60')),       # < 1000 years: minutes
        (Decimal(YEAR * 10000),    Decimal('3600')),     # < 10K years: hours
        (Decimal(YEAR * 100000),   Decimal('86400')),    # < 100K years: days
        (Decimal(YEAR * 1000000),  Decimal('2592000')),  # < 1M years: months
        (Decimal(YEAR * 10000000), Decimal('31556925')), # < 10M years: years
    ]
    
    # Find appropriate minimum unit value
    min_unit_value = Decimal('1e-9')  # default to microseconds
    for range_seconds, min_value in TIME_RANGES:
        if abs_seconds < range_seconds:
            break
        min_unit_value = min_value
    
    logger.debug(f"Time value: {abs_seconds} seconds")
    logger.debug(f"Selected minimum unit value: {min_unit_value}")
    
    # Filter units
    relevant_units = [
        unit for unit in unit_list
        if Decimal(unit.value) >= min_unit_value
    ]
    
    logger.debug(f"Filtered units: {[u.abbreviation for u in relevant_units]}")
    return relevant_units

class UnitsFormatter(FormatterProtocol):
    def format(self, total_seconds: Decimal, units: FixedUnitManagerProtocol, 
               uncertainty: TimeUncertainty, options: dict) -> str:
        opts = FormattingOptions(**options)
        # Get the units to use
        if opts.units:
            # Use specifically requested units
            unit_list = [units.get_unit(u) for u in opts.units]
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

    def _calculate_unit_values(self, total_seconds: Decimal, 
                             unit_list: List) -> Dict[str, Decimal]:
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
                
            result[unit.abbreviation] = count
                
        return result

    def _format_result(self, total_seconds: Decimal,
                      result: Dict[str, Decimal],
                      units: FixedUnitManagerProtocol,
                      uncertainty: TimeUncertainty,
                      opts: FormattingOptions) -> str:
        if opts.notation != NotationType.STANDARD:
            return self._format_scientific(total_seconds, uncertainty, opts)
        
        return self._format_units(result, units, opts)

    def _format_units(self, result: Dict[str, Decimal],
                     units: FixedUnitManagerProtocol,
                     opts: FormattingOptions) -> str:
        parts = []
        style = opts.style
        for unit_abbrev, count in result.items():
            unit = units.get_unit(unit_abbrev)
            
            # Format the count
            if isinstance(count, Decimal) and count % 1 != 0:
                value_str = f"{count:.2f}"
            else:
                value_str = f"{int(count)}"
            
            if style == 'full':
                unit_name = unit.name + ('s' if count != 1 else '')
                unit_str = unit_name if opts.raw else ColorFormatter.green(unit_name)
                parts.append(f"{value_str} {unit_str}")
            elif style == 'short':
                unit_str = unit_abbrev if opts.raw else ColorFormatter.green(unit_abbrev)
                parts.append(f"{value_str}{unit_str}")
            elif style == 'compact':
                unit_str = unit_abbrev if opts.raw else ColorFormatter.green(unit_abbrev)
                parts.append(f"{value_str}{unit_str}")

        if style == 'compact':
            return "".join(parts)
        elif style == 'full':
            return ", ".join(parts)
        else:  # short
            return " ".join(parts)


    def _get_meaningful_units(self, total_seconds: Decimal, 
                             uncertainty: TimeUncertainty,
                             units: FixedUnitManagerProtocol) -> List:
        decimal_units = sorted(
            units.get_units_by_groups(["decimal", "scientific", "second"], True),
            key=lambda u: Decimal(u.value),
            reverse=True
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

            logger.debug(f"Unit {unit.abbreviation}: value={unit_value}, "
                        f"abs_unc={abs_uncertainty}, rel_unc={rel_uncertainty}, "
                        f"effective_unc={effective_uncertainty}")

            # Skip if uncertainty is larger than unit value
            if effective_uncertainty >= unit_value:
                break

            # Calculate how many of this unit we have
            count = remaining // unit_value

            # Only include units with non-zero values
            if count > 0:
                meaningful_units.append(unit)
                remaining %= unit_value
                logger.debug(f"Added unit {unit.abbreviation} (count={count}, remaining={remaining})")

        # Always include at least one unit
        if not meaningful_units and relevant_units:
            meaningful_units.append(relevant_units[-1])

        return meaningful_units


# class UnitsFormatter(FormatterProtocol):
#     def __init__(self, config: Optional[FormatterConfig] = None):
#         self.config = config or FormatterConfig()

#     def format(self, total_seconds: Decimal, units: FixedUnitManagerProtocol, 
#                uncertainty: TimeUncertainty, options: dict) -> str:
#         opts = FormattingOptions(**options)
#         if "units" in options:
#             unit_list = [units.get_unit(u) for u in options["units"]]
#             breakpoint()
#         if opts.style == "scientific":
#             formatted = self._format_scientific(total_seconds, uncertainty, opts)
#         else:
#             meaningful_units = self._get_meaningful_units(total_seconds, uncertainty, units)

#             if not meaningful_units:
#                 return "No appropriate unit found"

#             result = self._calculate_unit_values(total_seconds, meaningful_units)
#             formatted = self._format_result(total_seconds, result, units, uncertainty, opts)
#         return self._add_prefix(formatted, total_seconds, opts.raw)

    # def _get_meaningful_units(self, total_seconds: Decimal, 
    #                         uncertainty: TimeUncertainty,
    #                         units: FixedUnitManagerProtocol) -> List:
    #     effective_uncertainty = uncertainty.get_effective_uncertainty(total_seconds)
    #     decimal_units = sorted(
    #         units.get_units_by_groups(["decimal", "scientific", "second"], True),
    #         key=lambda u: Decimal(u.value),
    #         reverse=True
    #     )

    #     return [
    #         unit for unit in decimal_units
    #         if (Decimal(unit.value) >= effective_uncertainty and
    #             Decimal(unit.value) <= abs(total_seconds))
    #     ]

#     def _calculate_unit_values(self, total_seconds: Decimal, 
#                              units: List) -> Dict[str, int]:
#         result = {}
#         remaining = abs(total_seconds)
        
#         for unit in units:
#             unit_value = Decimal(unit.value)
#             count = remaining // unit_value
#             if count > 0:
#                 remaining %= unit_value
#                 result[unit.abbreviation] = int(count)
                
#         return result

#     def _format_result(self, total_seconds: Decimal,
#                       result: Dict[str, int],
#                       units: FixedUnitManagerProtocol,
#                       uncertainty: TimeUncertainty,
#                       opts: FormattingOptions) -> str:
#         if opts.style == 'scientific':
#             return self._format_scientific(
#                 total_seconds, 
#                 uncertainty, 
#                 opts.show_confidence
#             )
        
#         return self._format_units(result, units, opts.style)

#     def _format_scientific(self, value: Decimal, 
#                          uncertainty: TimeUncertainty,
#                          opts: FormattingOptions) -> str:
#         """Format value in scientific notation."""
#         if opts.notation == NotationType.SCIENTIFIC:
#             value_str = f"{abs(value):.2e}"  # 1.74e+9
#             if opts.show_uncertainty:
#                 uncert = uncertainty.get_effective_uncertainty(value)
#                 uncert_str = f"{uncert:.2e}"
#                 formatted = f"{value_str} ± {uncert_str}"
#                 if opts.show_confidence and uncertainty.confidence_95:
#                     low, high = uncertainty.confidence_95
#                     formatted += f" (95% CI: {low:.2e}-{high:.2e})"
#                 return formatted
#             return value_str

#         elif opts.notation == NotationType.ENGINEERING:
#             # Convert to engineering notation (powers of 3)
#             exp = value.adjusted()
#             eng_exp = (exp // 3) * 3
#             mantissa = value / Decimal(10) ** eng_exp
#             value_str = f"{mantissa:.3f}×10{self._superscript(eng_exp)}"
            
#             if opts.show_uncertainty:
#                 uncert = uncertainty.get_effective_uncertainty(value)
#                 uncert_mantissa = uncert / Decimal(10) ** eng_exp
#                 return f"{value_str} ± {uncert_mantissa:.3f}×10{self._superscript(eng_exp)}"
#             return value_str

#         elif opts.notation == NotationType.MEASUREMENT:
#             # Compact measurement notation with uncertainty in parentheses
#             exp = value.adjusted()
#             eng_exp = (exp // 3) * 3
#             mantissa = value / Decimal(10) ** eng_exp
#             uncert = uncertainty.get_effective_uncertainty(value)
#             uncert_mantissa = uncert / Decimal(10) ** eng_exp
#             # Format as 1.738809452(174)×10⁹
#             return f"{mantissa:.9f}({int(uncert_mantissa*1e9)})×10{self._superscript(eng_exp)}"

#         return f"{abs(value):.2f}"

#     def _superscript(self, n: int) -> str:
#         """Convert number to superscript."""
#         superscript_map = str.maketrans("0123456789+-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻")
#         return str(n).translate(superscript_map)



#     # def _format_scientific(self, value: Decimal, 
#     #                      uncertainty: TimeUncertainty,
#     #                      show_confidence: bool) -> str:
#     #     effective_uncertainty = uncertainty.get_effective_uncertainty(value)
#     #     formatted = f"{abs(value):.2f} ± {effective_uncertainty:.2f}"
        
#     #     if show_confidence and uncertainty.confidence_95:
#     #         low, high = uncertainty.confidence_95
#     #         formatted += f" (95% CI: {low:.2f}-{high:.2f})"
            
#     #     return formatted

#     def _format_units(self, result: Dict[str, int],
#                      units: FixedUnitManagerProtocol,
#                      style: str) -> str:
#         if style == 'full':
#             parts = [f"{count} {units.get_unit(unit).name}s" 
#                     for unit, count in result.items()]
#             return ", ".join(parts)
            
#         elif style == 'short':
#             parts = [f"{count}{unit}" 
#                     for unit, count in result.items()]
#             return " ".join(parts)
            
#         elif style == 'compact':
#             parts = [f"{count}{unit}" 
#                     for unit, count in result.items()]
#             return "".join(parts)
            
#         return ""

    def _add_prefix(self, formatted: str, value: Decimal, raw: bool) -> str:
        if raw:
            return ("+" if value > 0 else "-") + formatted
        return (ColorFormatter.green("  + ") if value > 0 
                else ColorFormatter.red("  - ")) + formatted




#     def _format_uncertainty(self, value: Decimal) -> str:
#         """Format uncertainty value."""
#         if self.config.show_percentage:
#             formatted = f"{value * 100:.{self.config.significant_digits}f}%"
#         else:
#             formatted = f"{value:.{self.config.significant_digits}f}"
            
#         if self.config.color_uncertainty:
#             return ColorFormatter.yellow(formatted)
#         return formatted

#     def _format_confidence_interval(self, lower: Decimal, upper: Decimal) -> str:
#         """Format confidence interval."""
#         formatted = f"({self.config.confidence_level * 100:.0f}% CI: {lower:.{self.config.significant_digits}f}-{upper:.{self.config.significant_digits}f})"
        
#         if self.config.color_uncertainty:
#             return ColorFormatter.yellow(formatted)
#         return formatted

