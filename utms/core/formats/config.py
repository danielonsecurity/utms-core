from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum, auto
from typing import Optional

class UncertaintyDisplay(Enum):
    NONE = auto()          # Just the value
    SIMPLE = auto()        # Value ± uncertainty
    CONFIDENCE = auto()    # Value (95% CI: range)
    BOTH = auto()          # Value ± uncertainty (95% CI: range)

@dataclass
class FormatterConfig:
    uncertainty_display: UncertaintyDisplay = UncertaintyDisplay.NONE
    confidence_level: Decimal = Decimal("0.95")  # 95% confidence interval
    show_percentage: bool = False                # Show uncertainty as percentage
    color_uncertainty: bool = True               # Use colors for uncertainty values
    significant_digits: int = 2                  # Number of digits for uncertainty

@dataclass
class TimeUncertainty:
    absolute: Decimal = Decimal("1")   # smallest meaningful unit, i.e. 1e-9 for nanoseconds, default to second level precision
    relative: Decimal = Decimal("0")   # relative uncairtainty (0.02 for 2%), default to absolute
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
