from decimal import Decimal
from typing import Optional, Dict, Any

from utms.utms_types import FixedUnitManagerProtocol
from ...utils import ColorFormatter
from .base import FormatterProtocol
from .config import TimeUncertainty

class CalendarFormatter(FormatterProtocol):
    """Formats time as YYYY-MM-DD."""
    
    def format(self, total_seconds: Decimal, units: FixedUnitManagerProtocol, uncertainty: TimeUncertainty, options: dict) -> str:
        result = {}
        remaining = abs(total_seconds)

        # Calculate Y/M/D values with proper remainder handling
        unit_sequence = ["Y", "M", "d"]
        for i, unit in enumerate(unit_sequence):
            unit_info = units.get_unit(unit)
            if not unit_info:
                continue

            unit_value = Decimal(unit_info.value)
            
            if i == len(unit_sequence) - 1:
                # For the last unit (days), include fractional part
                count = remaining / unit_value
            else:
                # For years and months, use integer division
                count = remaining // unit_value
                remaining %= unit_value  # Pass remainder to next unit
            
            result[unit] = int(count)  # Convert to int for display

        # # Calculate Y/M/D values
        # for unit in ["Y", "M", "D"]:
        #     unit_info = units.get_unit(unit)
        #     if not unit_info:
        #         continue

        #     unit_value = unit_info.value
        #     count = remaining // unit_value
        #     remaining %= unit_value
        #     result[unit] = int(count)

        # Get formatting options
        raw = options.get('raw', False)
        style = options.get('style', 'full')  # 'full', 'short', 'compact'

        if style == 'full':  # "55 Years 01 Months 00 Days"
            if raw:
                prefix = "+" if total_seconds > 0 else "-"
                return f"{prefix}{result['Y']:d} Years, {result['M']:02d} Months, {result['d']:02d} Days"
            else:
                prefix = ColorFormatter.green("  + ") if total_seconds > 0 else ColorFormatter.red("  - ")
                return f"{prefix}{result['Y']:d} {ColorFormatter.green('Years')} {result['M']:02d} {ColorFormatter.green('Months')} {result['d']:02d} {ColorFormatter.green('Days')} "

        elif style == 'short':  # "55 Y 01 M 00 D"
            if raw:
                formatted = f"{result['Y']} 'Y' {result['M']:02d} 'M' {result['d']:02d} 'd'"
                prefix = "+" if total_seconds > 0 else "-"
                return prefix + formatted
            else:
                formatted = f"{result['Y']} {ColorFormatter.green('Y')} {result['M']:02d} {ColorFormatter.green('M')} {result['d']:02d} {ColorFormatter.green('d')}"
                prefix = ColorFormatter.green("  + ") if total_seconds > 0 else ColorFormatter.red("  - ")
                return prefix + formatted

        elif style == 'compact':  # "55Y01M00D"
            if raw:
                formatted = f"{result['Y']}Y{result['M']:02d}M{result['d']:02d}d"
                prefix = "+" if total_seconds > 0 else "-"
                return prefix + formatted
            else:
                formatted = f"{result['Y']}{ColorFormatter.green('Y')}{result['M']:02d}{ColorFormatter.green('M')}{result['d']:02d}{ColorFormatter.green('d')}"
                prefix = ColorFormatter.green("  + ") if total_seconds > 0 else ColorFormatter.red("  - ")
                return prefix + formatted
