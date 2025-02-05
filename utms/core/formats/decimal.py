from decimal import Decimal

from utms.utms_types import FixedUnitManagerProtocol
from ...utils import ColorFormatter
from .base import FormatterProtocol

from typing import Optional

from .config import FormatterConfig, UncertaintyDisplay


class DecimalFormatter(FormatterProtocol):
    def __init__(self, config: Optional[FormatterConfig] = None):
        self.config = config or FormatterConfig()

    def format(self, total_seconds: Decimal, units: FixedUnitManagerProtocol, precision: Decimal) -> str:
        decimal_units = sorted(
            units.get_units_by_groups(["decimal", "scientific"], True),
            key=lambda u: Decimal(u.value),
            reverse=True
        )
        
        # Calculate the smallest meaningful unit given the precision
        absolute_uncertainty = abs(total_seconds) * Decimal(precision)
        # Any unit smaller than this would be meaningless given our uncertainty
        smallest_meaningful_unit = absolute_uncertainty
        
        # Filter units
        meaningful_units = [
            unit for unit in decimal_units
            if Decimal(unit.value) >= smallest_meaningful_unit
        ]
        
        result = {}
        remaining = abs(total_seconds)
        
        for unit in meaningful_units:
            unit_value = Decimal(unit.value)
            count = remaining // unit_value
            if count > 0:
                remaining %= unit_value
                result[unit.abbreviation] = int(count)
        
        # Format output
        if total_seconds > 0:
            prefix = ColorFormatter.green("  + ")
        else:
            prefix = ColorFormatter.red("  - ")
            
        parts = [
            f"{count} {ColorFormatter.green(units.get_unit(unit).name + 's')}"
            for unit, count in result.items()
        ]
        
        return prefix + ", ".join(parts)




    def _format_uncertainty(self, value: Decimal) -> str:
        """Format uncertainty value."""
        if self.config.show_percentage:
            formatted = f"{value * 100:.{self.config.significant_digits}f}%"
        else:
            formatted = f"{value:.{self.config.significant_digits}f}"
            
        if self.config.color_uncertainty:
            return ColorFormatter.yellow(formatted)
        return formatted

    def _format_confidence_interval(self, lower: Decimal, upper: Decimal) -> str:
        """Format confidence interval."""
        formatted = f"({self.config.confidence_level * 100:.0f}% CI: {lower:.{self.config.significant_digits}f}-{upper:.{self.config.significant_digits}f})"
        
        if self.config.color_uncertainty:
            return ColorFormatter.yellow(formatted)
        return formatted

