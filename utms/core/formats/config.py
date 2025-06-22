from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum, auto
from typing import Optional


class UncertaintyDisplay(Enum):
    NONE = auto()  # Just the value
    SIMPLE = auto()  # Value ± uncertainty
    CONFIDENCE = auto()  # Value (95% CI: range)
    BOTH = auto()  # Value ± uncertainty (95% CI: range)


@dataclass
class TimeUncertainty:
    absolute: Decimal = Decimal(
        "1"
    )  # smallest meaningful unit, i.e. 1e-9 for nanoseconds, default to second level precision
    relative: Decimal = Decimal("0")  # relative uncairtainty (0.02 for 2%), default to absolute
    confidence_95: Optional[tuple[Decimal, Decimal]] = None

    def get_effective_uncertainty(self, value: Decimal) -> Decimal:
        """Get effective uncertainty, using larger of absolute/relative."""
        uncertainties = []

        if self.absolute is not None:
            uncertainties.append(self.absolute)

        if self.relative is not None:
            uncertainties.append(abs(value * self.relative))

        if not uncertainties:
            raise ValueError("No uncertainty specified")

        return max(uncertainties)

    def get_confidence_interval(self, value: Decimal) -> tuple[Decimal, Decimal]:
        """Calculate 95% confidence interval."""
        effective = self.get_effective_uncertainty(value)
        # For 95% confidence, multiply by 1.96 (assuming normal distribution)
        # interval = effective * Decimal("1.96")
        return (value - effective, value + effective)
