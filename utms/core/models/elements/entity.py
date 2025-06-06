from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

from utms.core.logger import get_logger
from utms.core.mixins.model import ModelMixin
from utms.utms_types.field.types import FieldType, TypedValue

logger = get_logger()


@dataclass
class Entity(ModelMixin):
    """
    Base class for all entities.
    Each attribute of a entity is stored as a TypedValue.
    Entities now also belong to a category.
    """

    name: str
    entity_type: str  # e.g., "task", "event"

    # Category defaults to "default", corresponds to filename (e.g., default.hy)
    category: str = field(default="default")

    attributes: Dict[str, TypedValue] = field(default_factory=dict)

    def __post_init__(self):
        if self.attributes is None:
            self.attributes = {}
        if not isinstance(self.category, str) or not self.category.strip():
            logger.warning(
                f"Entity '{self.name}' initialized with invalid category '{self.category}'. Defaulting to 'default'."
            )
            self.category = "default"
        else:
            self.category = self.category.strip().lower()  # Normalize category name

        # Ensure all attribute values are indeed TypedValue instances.
        for key, val in self.attributes.items():
            if not isinstance(val, TypedValue):
                logger.critical(  # Use critical as this indicates a programming error upstream
                    f"Entity '{self.name}' attribute '{key}' was not initialized with a TypedValue. "
                    f"Received type: {type(val)}. This must be fixed in the loader/manager."
                )
                # Not attempting to fix it here, as it indicates a larger issue.
                # An error should ideally be raised by the caller if this happens.
                # For robustness in case it slips through, it might be converted, but it's a bad sign.
                # For now, we assume the loader/manager correctly provides TypedValues.
                # If this Entity is being directly instantiated elsewhere, that code needs to be updated.
                pass

    def get_attribute_typed(self, attr_name: str) -> Optional[TypedValue]:
        return self.attributes.get(attr_name)

    def get_attribute_value(self, attr_name: str, default: Any = None) -> Any:
        typed_value = self.attributes.get(attr_name)
        return typed_value.value if typed_value else default

    def set_attribute_typed(self, attr_name: str, typed_value: TypedValue) -> None:
        if not isinstance(typed_value, TypedValue):
            raise ValueError(
                f"Value for attribute '{attr_name}' of entity '{self.name}' "
                f"must be a TypedValue instance. Got type: {type(typed_value)}"
            )
        self.attributes[attr_name] = typed_value

    def _set_attribute_from_loader(
        self,
        attr_name: str,
        raw_value_from_hy: Any,
        field_type_from_schema: Union[FieldType, str],
        is_dynamic_attr: bool = False,
        original_expr_str: Optional[str] = None,
        enum_choices_from_schema: Optional[List[Any]] = None,
        item_type_from_schema: Optional[Union[FieldType, str]] = None,
    ) -> None:
        self.attributes[attr_name] = TypedValue(
            value=raw_value_from_hy,
            field_type=field_type_from_schema,
            is_dynamic=is_dynamic_attr,
            original=original_expr_str,
            enum_choices=enum_choices_from_schema,
            item_type=item_type_from_schema,
        )

    def remove_attribute(self, attr_name: str) -> None:
        if attr_name in self.attributes:
            del self.attributes[attr_name]

    def has_attribute(self, attr_name: str) -> bool:
        return attr_name in self.attributes

    def is_attribute_dynamic(self, attr_name: str) -> bool:
        typed_value = self.attributes.get(attr_name)
        return typed_value.is_dynamic if typed_value else False

    def get_attribute_original_expression(self, attr_name: str) -> Optional[str]:
        typed_value = self.attributes.get(attr_name)
        return typed_value.original if typed_value and typed_value.is_dynamic else None

    def get_all_attributes_typed(self) -> Dict[str, TypedValue]:
        return self.attributes

    def __repr__(self) -> str:
        attrs_repr_parts = [f"{k}={repr(v)}" for k, v in self.attributes.items()]
        attrs_str = ", ".join(attrs_repr_parts)
        return (
            f"Entity(name='{self.name}', entity_type='{self.entity_type}', "
            f"category='{self.category}', attributes={{{attrs_str}}})"
        )

    def __hash__(self):
        # Category should be part of the identity if entities can have same name in different categories
        # but are considered different. For now, assuming name+type is unique across categories.
        # If name+type+category is unique, then include self.category in hash.
        return hash((self.entity_type, self.name))  # Current uniqueness

    def __eq__(self, other):
        if not isinstance(other, Entity):
            return False
        # Same consideration for self.category in equality
        return self.entity_type == other.entity_type and self.name == other.name
