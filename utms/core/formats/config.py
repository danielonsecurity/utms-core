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
