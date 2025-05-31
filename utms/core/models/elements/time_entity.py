# utms.core.models.elements.time_entity.py

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Union, List # Added List

from utms.core.mixins.model import ModelMixin
# Ensure these imports are correct based on your project structure
from utms.utms_types.field.types import TypedValue, FieldType 
from utms.core.logger import get_logger # For potential logging if needed

logger = get_logger()

@dataclass
class TimeEntity(ModelMixin):
    """
    Base class for all time entities.
    Each attribute of a time entity is stored as a TypedValue.
    """

    name: str  # The unique name of the entity instance
    entity_type: str  # The type of the entity (e.g., "task", "event")

    # attributes will store a dictionary where keys are attribute names (strings)
    # and values are TypedValue objects.
    attributes: Dict[str, TypedValue] = field(default_factory=dict)

    def __post_init__(self):
        if self.attributes is None: # Should be handled by default_factory
            self.attributes = {}
        
        # Ensure all attribute values are indeed TypedValue instances.
        # This is a safeguard; the loader should ideally guarantee this.
        attrs_to_convert = {}
        for key, val in self.attributes.items():
            if not isinstance(val, TypedValue):
                # This situation implies the loader/manager didn't prepare TypedValues correctly.
                # We'd need the schema context here to properly infer FieldType.
                # For now, log a warning and make a best-effort conversion.
                logger.warning(
                    f"TimeEntity '{self.name}': Attribute '{key}' initialized with raw value '{val}'. "
                    f"This should be handled by the loader. Attempting basic TypedValue conversion."
                )
                # Fallback: if schema isn't available here, infer_type is the best we can do.
                # from utms.utms_types.field.types import infer_type # Local import if needed
                # attrs_to_convert[key] = TypedValue(val, infer_type(val))
                # For safety, let's assume this path means an error in upstream logic.
                # It's better for the loader to create TypedValues with correct schema info.
                raise TypeError(
                    f"TimeEntity '{self.name}' attribute '{key}' must be initialized with a TypedValue. "
                    f"Received type: {type(val)}. Loader/Manager needs to ensure this."
                )
        # if attrs_to_convert:
        #    self.attributes.update(attrs_to_convert)


    def get_attribute_typed(self, attr_name: str) -> Optional[TypedValue]:
        """Gets the TypedValue object for a given attribute name."""
        return self.attributes.get(attr_name)

    def get_attribute_value(self, attr_name: str, default: Any = None) -> Any:
        """Gets the resolved Python value of a given attribute."""
        typed_value = self.attributes.get(attr_name)
        if typed_value:
            return typed_value.value
        return default

    def set_attribute_typed(self, attr_name: str, typed_value: TypedValue) -> None:
        """Sets an attribute using a pre-constructed TypedValue object."""
        if not isinstance(typed_value, TypedValue):
            raise ValueError(
                f"Value for attribute '{attr_name}' of entity '{self.name}' "
                f"must be a TypedValue instance. Got type: {type(typed_value)}"
            )
        self.attributes[attr_name] = typed_value

    # This method is primarily for use by the loader, which has schema context.
    def _set_attribute_from_loader(
        self, 
        attr_name: str, 
        raw_value_from_hy: Any, # Could be Hy object or already resolved Python value for dynamic
        field_type_from_schema: Union[FieldType, str], 
        is_dynamic_attr: bool = False,
        original_expr_str: Optional[str] = None,
        enum_choices_from_schema: Optional[List[Any]] = None,
        item_type_from_schema: Optional[Union[FieldType, str]] = None
    ) -> None:
        """
        Internal helper for loader to set an attribute by creating a TypedValue.
        'raw_value_from_hy' is the value to be stored/converted by TypedValue.
        For dynamic fields, this raw_value_from_hy should be the *resolved* Python value.
        For static fields, this raw_value_from_hy is the *raw Hy object*.
        """
        self.attributes[attr_name] = TypedValue(
            value=raw_value_from_hy,
            field_type=field_type_from_schema,
            is_dynamic=is_dynamic_attr,
            original=original_expr_str,
            enum_choices=enum_choices_from_schema,
            item_type=item_type_from_schema
        )

    def remove_attribute(self, attr_name: str) -> None:
        """Removes an attribute from the entity."""
        if attr_name in self.attributes:
            del self.attributes[attr_name]

    def has_attribute(self, attr_name: str) -> bool:
        """Checks if the entity has a given attribute."""
        return attr_name in self.attributes

    def is_attribute_dynamic(self, attr_name: str) -> bool:
        """Checks if a specific attribute is dynamic."""
        typed_value = self.attributes.get(attr_name)
        if typed_value:
            return typed_value.is_dynamic
        return False

    def get_attribute_original_expression(self, attr_name: str) -> Optional[str]:
        """Gets the original Hy expression for a dynamic attribute."""
        typed_value = self.attributes.get(attr_name)
        if typed_value and typed_value.is_dynamic:
            return typed_value.original
        return None
    
    def get_all_attributes_typed(self) -> Dict[str, TypedValue]:
        """Returns the entire dictionary of attributes with their TypedValues."""
        return self.attributes

    def __repr__(self) -> str:
        attrs_repr_parts = []
        for k, v_typed in self.attributes.items():
            attrs_repr_parts.append(f"{k}={repr(v_typed)}") # Uses TypedValue.__repr__
        attrs_str = ", ".join(attrs_repr_parts)
        return f"TimeEntity(name='{self.name}', entity_type='{self.entity_type}', attributes={{{attrs_str}}})"

    def __hash__(self):
        return hash((self.entity_type, self.name))

    def __eq__(self, other):
        if not isinstance(other, TimeEntity):
            return False
        return self.entity_type == other.entity_type and self.name == other.name
