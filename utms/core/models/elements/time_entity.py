from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from utms.core.mixins.model import ModelMixin


@dataclass
class TimeEntity(ModelMixin):
    """
    Base class for all time entities.
    
    A time entity represents any object with time-related properties.
    This is a minimal implementation with no predefined attributes,
    allowing users to define exactly what they need.
    """

    name: str
    entity_type: str
    attributes: Dict[str, Any] = field(default_factory=dict)
    dynamic_fields: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def __post_init__(self):
        # Initialize collections if not provided
        if self.attributes is None:
            self.attributes = {}
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
        if field_name in ["name", "entity_type"]:
            setattr(self, field_name, value)
        else:
            self.attributes[field_name] = value
            
        self.dynamic_fields[field_name] = {
            'original': original,
            'value': value
        }

    def get_attribute(self, attr_name: str, default: Any = None) -> Any:
        """Get an attribute value with optional default."""
        return self.attributes.get(attr_name, default)

    def set_attribute(self, attr_name: str, value: Any) -> None:
        """Set an attribute value."""
        self.attributes[attr_name] = value

    def has_attribute(self, attr_name: str) -> bool:
        """Check if an attribute exists."""
        return attr_name in self.attributes

    def __repr__(self) -> str:
        return f"TimeEntity(name={self.name}, type={self.entity_type}, attributes={self.attributes})"

    def __hash__(self):
        return hash((self.entity_type, self.name))

    def __eq__(self, other):
        if not isinstance(other, TimeEntity):
            return False
        return self.entity_type == other.entity_type and self.name == other.name
