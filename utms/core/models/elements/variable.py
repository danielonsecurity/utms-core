from dataclasses import dataclass, field
from typing import Any, Optional, Dict

from utms.core.mixins.model import ModelMixin


@dataclass
class Variable(ModelMixin):
    """Represents a variable with its properties."""

    key: str
    value: Any
    dynamic_fields: Dict[str, Dict[str, Any]] = field(default_factory=dict)


    def __post_init__(self):
        # Initialize dynamic_fields if not provided
        if self.dynamic_fields is None:
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
        return f"Variable(key={self.key}, value={self.value}{dynamic_info})"

    def __hash__(self):
        return hash(self.key)

    def __eq__(self, other):
        if not isinstance(other, Variable):
            return False
        return self.key == other.key

    def format_field(self, field_name: str) -> str:
        """Format a field value for display, showing dynamic info if applicable."""
        value = getattr(self, field_name)
        if self.is_field_dynamic(field_name):
            original = self.get_original_expression(field_name)
            return f"{value} (dynamic: {original})"
        return str(value)
