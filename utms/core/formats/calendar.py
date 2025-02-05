from decimal import Decimal

from utms.utms_types import FixedUnitManagerProtocol
from ...utils import ColorFormatter
from .base import FormatterProtocol

class CalendarFormatter(FormatterProtocol):
    """Formats time as YYYY-MM-DD."""
    
    def format(self, total_seconds: Decimal, units: FixedUnitManagerProtocol, precision: Decimal) -> str:
        result = {}
        remaining = abs(total_seconds)
        if total_seconds > 0:
            prefix = ColorFormatter.green("  + ")
        else:
            prefix = ColorFormatter.red(" - ")
        
        # Calculate values for Y/M/D
        for unit in ["Y", "M", "D"]:
            unit_info = units.get_unit(unit)
            if not unit_info:
                continue
                
            unit_value = Decimal(unit_info.value)
            count = remaining // unit_value
            remaining %= unit_value
            result[unit] = int(count)
            
        return prefix + f"{result['Y']:d} {ColorFormatter.green('Years')} {result['M']:02d}  {ColorFormatter.green('Months')} {result['D']:02d}  {ColorFormatter.green('Days')} "
