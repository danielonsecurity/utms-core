# money.py
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, Optional

from utms.core.formats.base import FormattingOptions
from utms.utms_types import FixedUnitManagerProtocol

from ...utils import ColorFormatter
from .base import FormatterProtocol
from .config import TimeUncertainty


class MoneyFormatter(FormatterProtocol):
    def format(
        self,
        total_seconds: Decimal,
        units: FixedUnitManagerProtocol,
        uncertainty: TimeUncertainty,
        options: dict,
    ) -> str:
        # Get options
        opts = FormattingOptions(**options)
        currency = opts.currency
        position_right = opts.position_right
        compact = opts.compact
        show_rate = opts.show_rate
        signed = opts.signed
        indented = opts.indented
        base_unit = opts.base_unit
        rate = opts.rate
        raw = opts.raw

        # Get base unit information from unit manager
        unit_info = units.get(base_unit)
        if not unit_info:
            raise ValueError(f"Invalid base unit: {base_unit}")

        # Calculate conversion to base unit
        base_unit_value = Decimal(unit_info.value)
        base_units = total_seconds / base_unit_value

        # Calculate money amount
        amount = base_units * rate

        # Format currency symbol
        symbol = currency if raw else ColorFormatter.green(currency)

        # Format the amount
        amount_str = f"{abs(amount):,.2f}"

        # Space between amount and currency based on compact
        space = "" if compact else " "

        # Combine amount and currency based on position
        if position_right:
            value_str = f"{amount_str}{space}{symbol}"
        else:
            value_str = f"{symbol}{space}{amount_str}"

        # Add rate information if requested
        if show_rate:
            rate_str = f"{rate}{space}"
            rate_str += currency if raw else ColorFormatter.green(currency)
            rate_str += "/" if raw else ColorFormatter.magenta("/")
            rate_str += (
                unit_info.abbreviation if raw else ColorFormatter.green(unit_info.abbreviation)
            )
            value_str += f"{space}@{space}{rate_str}"

        # Add sign and indentation
        if signed:
            if total_seconds < 0:
                sign = "-" if raw else ColorFormatter.red("-")
            else:
                sign = "+" if raw else ColorFormatter.green("+")
        else:
            sign = ""

        if indented:
            result = "  "
        else:
            result = ""
        if signed:
            result += sign
        if not compact:
            result += " "
            if not signed:
                result += " "
        result += value_str

        return result
