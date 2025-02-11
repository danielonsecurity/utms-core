from dataclasses import dataclass
from decimal import Decimal
from typing import List

@dataclass
class UnitConfig:
    label: str
    name: str
    value: Decimal
    groups: List[str]
