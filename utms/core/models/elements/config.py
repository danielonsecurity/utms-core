from dataclasses import dataclass, field
from typing import Any, List, Optional, Union, Dict

from utms.core.mixins.model import ModelMixin
from utms.utms_types import TypedValue, FieldType, infer_type


@dataclass
class Config(ModelMixin):
    """Represents a configuration entry with its properties."""

    key: str
    value: TypedValue

    def __post_init__(self):
        # Ensure value is a TypedValue
        if not isinstance(self.value, TypedValue):
            self.value = TypedValue(self.value, infer_type(self.value))

    def is_field_dynamic(self, field_name: str) -> bool:
        """Check if a specific field is dynamic."""
        if field_name != "value":
            # We only support the 'value' field for now in Config objects
            return False
        
        return self.value.is_dynamic

    def get_original_expression(self, field_name: str) -> Optional[str]:
        """Get the original expression for a dynamic field."""
        if not self.is_field_dynamic(field_name):
            return None
            
        if field_name == "value":
            return self.value.original
            
        return None

    def set_dynamic_field(self, field_name: str, value: Any, original: str) -> None:
        """Set a field as dynamic with its original expression."""
        if field_name != "value":
            raise ValueError(f"Dynamic fields are only supported for 'value', got {field_name}")
            
        # Create a TypedValue with dynamic properties
        field_type = self.value.field_type if isinstance(self.value, TypedValue) else infer_type(value)
        self.value = TypedValue(
            value, 
            field_type,
            is_dynamic=True,
            original=original
        )

    def get_value(self) -> Any:
        """Get the actual value from the TypedValue."""
        return self.value.value

    def get_value_type(self) -> FieldType:
        """Get the type of the value."""
        return self.value.field_type

    def __repr__(self) -> str:
        value_info = f"value={self.value.value} (type={self.value.field_type.value})"
        if self.value.is_dynamic:
            value_info += f" (dynamic: {self.value.original})"
            
        return f"Config(key={self.key}, {value_info})"

    def __hash__(self):
        return hash(self.key)

    def __eq__(self, other):
        if not isinstance(other, Config):
            return False
        return self.key == other.key

    def format_field(self, field_name: str) -> str:
        """Format a field value for display, showing dynamic info if applicable."""
        if field_name != "value":
            raise ValueError(f"Config only supports 'value' field, got {field_name}")
            
        display_value = self.value.value
        
        if self.value.is_dynamic:
            return f"{display_value} (dynamic: {self.value.original})"
            
        return f"{display_value} (type: {self.value.field_type.value})"
