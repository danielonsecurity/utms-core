from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol, Optional, Dict, Any, List
from enum import Enum

from utms.utms_types import FixedUnitManagerProtocol
from .config import TimeUncertainty

class FormatterProtocol(Protocol):
    """Base protocol for all formatters."""
    def format(self, total_seconds: Decimal, units: FixedUnitManagerProtocol, uncertainty: TimeUncertainty, options: Optional[Dict[str, Any]]) -> str:
        """Format total_seconds using the given units."""
        ...

class NotationType(Enum):
    STANDARD = "standard"
    SCIENTIFIC = "scientific"    # 1.74e+9
    ENGINEERING = "engineering"  # 1.74×10⁹
    MEASUREMENT = "measurement"  # 1.738809452(174)×10⁹

@dataclass
class FormattingOptions:
    style: str = "full"
    abbreviated: bool = False
    raw: bool = False
    show_uncertainty: bool = False
    show_confidence: bool = False
    signed: bool = True
    compact: bool = False
    separator: str = " + "
    plural: bool = True
    indented: bool = True
    notation: NotationType = NotationType.STANDARD
    units: Optional[List[str]] = None

    def __post_init__(self):
        if isinstance(self.notation, str):
            self.notation = NotationType(self.notation)
        # Convert units to list if it's a single string
        if isinstance(self.units, str):
            self.units = [self.units]
        # Ensure units is always a list or None
        elif self.units is not None and not isinstance(self.units, list):
            self.units = list(self.units)

        # Convert string booleans
        for attr in ['abbreviated', 'raw', 'signed', 'compact', 'show_uncertainty', 'show_confidence', 'plural', 'indented']:
            value = getattr(self, attr)
            if isinstance(value, str):
                setattr(self, attr, value.lower() == "true")
        
