from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from utms.core.mixins.model import ModelMixin
from utms.utms_types.field.types import TypedValue


@dataclass
class Variable(ModelMixin):
    """Represents a variable with its properties."""

    key: str
    value: TypedValue

    def __post_init__(self):
        if not isinstance(self.value, TypedValue):
            self.logger.warning(
                f"Variable '{self.key}' value was not initialized as a TypedValue. "
                f"Wrapped it as a STRING TypedValue. This should be fixed upstream."
            )

    def is_field_dynamic(self, field_name: str) -> bool:
        """Check if a specific field (only 'value' for now) is dynamic."""
        if field_name == "value":
            return self.value.is_dynamic
        return False

    def get_original_expression(self, field_name: str) -> Optional[str]:
        """Get the original expression for a dynamic field."""
        if field_name == "value":
            return self.value.original
        return None

    def __repr__(self) -> str:
        # Simplified repr
        return f"Variable(key='{self.key}', value={repr(self.value)})"

    def __hash__(self):
        return hash(self.key)

    def __eq__(self, other):
        if not isinstance(other, Variable):
            return False
        return self.key == other.key

    def format_field(self, field_name: str) -> str:
        """Format a field value for display, showing dynamic info if applicable."""
        if field_name == "value":
            return str(self.value)  # TypedValue.__str__ handles dynamic display
        return str(getattr(self, field_name))  # For other potential fields
