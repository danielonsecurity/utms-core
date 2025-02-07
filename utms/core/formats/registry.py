from decimal import Decimal
from typing import Dict, Type

from utms.utms_types import FixedUnitManagerProtocol
from .base import FormatterProtocol
from .calendar import CalendarFormatter
from .scientific import ScientificFormatter
from .config import TimeUncertainty
from .units import UnitsFormatter

class FormatRegistry:
    """Central registry for different format types."""
    
    def __init__(self):
        self._formatters: Dict[str, FormatterProtocol] = {}
        self._setup_default_formatters()

    def _setup_default_formatters(self) -> None:
        self.register("CALENDAR", CalendarFormatter())
        self.register("UNITS", UnitsFormatter())
        self.register("SCIENTIFIC", ScientificFormatter())

    def register(self, name: str, formatter: FormatterProtocol) -> None:
        """Register a new formatter."""
        self._formatters[name] = formatter

    def get_formatter(self, name: str) -> FormatterProtocol:
        """Get a formatter by name."""
        if name not in self._formatters:
            raise ValueError(f"Unknown format: {name}")
        return self._formatters[name]

    def format(self, format_name: str, total_seconds: Decimal, units: FixedUnitManagerProtocol, uncertainty: TimeUncertainty, options) -> str:
        """Format using the specified formatter."""
        formatter = self.get_formatter(format_name)
        return formatter.format(total_seconds, units, uncertainty, options)

    @property
    def available_formats(self) -> list[str]:
        """List all registered format names."""
        return list(self._formatters.keys())

registry = FormatRegistry()    
