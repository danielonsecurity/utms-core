from decimal import Decimal
from typing import Any, Dict, Optional

from utms.utms_types import FixedUnitManagerProtocol

from ...utils import ColorFormatter
from .base import DateTimeFormatterBase, FormatterProtocol
from .config import TimeUncertainty


class CalendarFormatter(DateTimeFormatterBase):
    """Formats time as YYYY-MM-DD."""

    UNIT_SEQUENCE = ["Y", "M", "d"]
    UNIT_LABELS = {"Y": "Years", "M": "Months", "d": "Days"}

    def format(
        self,
        total_seconds: Decimal,
        units: FixedUnitManagerProtocol,
        uncertainty: TimeUncertainty,
        options: dict,
    ) -> str:
        result = {}
        remaining = abs(total_seconds)

        # Calculate Y/M/D values with proper remainder handling
        for i, unit in enumerate(self.UNIT_SEQUENCE):
            unit_info = units.get_unit(unit)
            if not unit_info:
                continue

            unit_value = Decimal(unit_info.value)

            if i == len(self.UNIT_SEQUENCE) - 1:
                # For the last unit (days), include fractional part
                count = remaining / unit_value
            else:
                # For years and months, use integer division
                count = remaining // unit_value
                remaining %= unit_value  # Pass remainder to next unit

            result[unit] = int(count)  # Convert to int for display

        return self._format_with_style(
            result,
            self.UNIT_LABELS,
            total_seconds,
            options.get("style", "full"),
            options.get("raw", False),
        )
