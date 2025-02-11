from decimal import Decimal
from typing import Any, Dict, Optional

from utms.utms_types import FixedUnitManagerProtocol

from ...utils import ColorFormatter
from .base import DateTimeFormatterBase, FormatterProtocol
from .config import TimeUncertainty


class DateTimeFormatter(DateTimeFormatterBase):
    """Combines calendar and clock formatting."""

    UNIT_SEQUENCE = ["Y", "M", "d", "h", "m", "s"]
    UNIT_LABELS = {
        "Y": "Years",
        "M": "Months",
        "d": "Days",
        "h": "Hours",
        "m": "Minutes",
        "s": "Seconds",
    }

    def format(
        self,
        total_seconds: Decimal,
        units: FixedUnitManagerProtocol,
        uncertainty: TimeUncertainty,
        options: dict,
    ) -> str:
        result = {}
        remaining = abs(total_seconds)

        for i, unit in enumerate(self.UNIT_SEQUENCE):
            unit_info = units.get_unit(unit)
            if not unit_info:
                continue

            unit_value = Decimal(unit_info.value)

            if i == len(self.UNIT_SEQUENCE) - 1:
                count = remaining / unit_value
            else:
                count = remaining // unit_value
                remaining %= unit_value

            result[unit] = int(count)

        return self._format_with_style(
            result,
            self.UNIT_LABELS,
            total_seconds,
            options.get("style", "full"),
            options.get("raw", False),
        )
