from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional

from utms.utms_types import HyProperty, UnitConfig

from ..mixins.model import ModelMixin


@dataclass
class FixedUnit(ModelMixin):
    """Represents a fixed time unit with its properties."""

    label: str
    name: str
    value: Decimal
    groups: Optional[List[str]] = None

    def __post_init__(self):
        if self.groups is None:
            self.groups = []

    def __repr__(self) -> str:
        return f"FixedUnit(name={self.name}, label={self.label}, value={self.value}, groups={self.groups})"

    def convert_to(self, other: "FixedUnit", value: Decimal) -> Decimal:
        """Converts a value from this unit to another unit."""
        return value * (self.value / other.value)
