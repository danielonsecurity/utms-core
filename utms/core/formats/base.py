from decimal import Decimal
from typing import Protocol

from utms.utms_types import FixedUnitManagerProtocol

class FormatterProtocol(Protocol):
    """Base protocol for all formatters."""
    def format(self, total_seconds: Decimal, units: FixedUnitManagerProtocol, precision: Decimal) -> str:
        """Format total_seconds using the given units."""
        ...
