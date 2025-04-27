from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Dict, List, Optional

from utms.utms_types import HyProperty, UnitConfig

from utms.core.mixins.model import ModelMixin


@dataclass
class Unit(ModelMixin):
    """Represents a time unit with its properties."""

    label: str
    name: Any
    value: Any
    groups: Optional[List[Any]] = None
    
    # Track dynamic status for each field
    dynamic_fields: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def __post_init__(self):
        if self.groups is None:
            self.groups = []
        
        # Initialize dynamic_fields if not provided
        if not self.dynamic_fields:
            self.dynamic_fields = {}

    def is_field_dynamic(self, field_name: str) -> bool:
        """Check if a specific field is dynamic."""
        return field_name in self.dynamic_fields

    def get_original_expression(self, field_name: str) -> Optional[str]:
        """Get the original expression for a dynamic field."""
        if not self.is_field_dynamic(field_name):
            return None
        return self.dynamic_fields.get(field_name, {}).get('original')

    def set_dynamic_field(self, field_name: str, value: Any, original: str) -> None:
        """Set a field as dynamic with its original expression."""
        setattr(self, field_name, value)
        self.dynamic_fields[field_name] = {
            'original': original,
            'value': value
        }

    def __repr__(self) -> str:
        dynamic_info = ""
        if self.dynamic_fields:
            dynamic_info = f", dynamic_fields={self.dynamic_fields}"
        return f"Unit(name={self.name}, label={self.label}, value={self.value}, groups={self.groups}{dynamic_info})"

    def convert_to(self, other: "Unit", value: Decimal) -> Decimal:
        """Converts a value from this unit to another unit."""
        # Ensure we're using Decimal values for the calculation
        self_value = self.value if isinstance(self.value, Decimal) else Decimal(str(self.value))
        other_value = other.value if isinstance(other.value, Decimal) else Decimal(str(other.value))
        return value * (self_value / other_value)

    def format_field(self, field_name: str) -> str:
        """Format a field value for display, showing dynamic info if applicable."""
        value = getattr(self, field_name)
        if self.is_field_dynamic(field_name):
            original = self.get_original_expression(field_name)
            return f"{value} (dynamic: {original})"
        return str(value)
