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
    source_file: Optional[str] = field(default=None, repr=False) 
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
                pass
        normalized_attributes = {}
        for key, val in self.attributes.items():
            canonical_key = self._normalize_key(key)
            if canonical_key in normalized_attributes:
                logger.warning(
                    f"Duplicate attribute key after normalization for '{key}' (becomes '{canonical_key}') "
                    f"on entity '{self.name}'. The last one provided will be used."
                )
            normalized_attributes[canonical_key] = val
        self.attributes = normalized_attributes

    def _normalize_key(self, key: str) -> str:
        """Converts any key to the canonical kebab-case form."""
        return str(key).replace('_', '-')

    def get_attribute_typed(self, attr_name: str) -> Optional[TypedValue]:
        canonical_name = self._normalize_key(attr_name)
        return self.attributes.get(canonical_name)

    def get_attribute_value(self, attr_name: str, default: Any = None) -> Any:
        typed_value = self.get_attribute_typed(attr_name)
        return typed_value.value if typed_value else default

    def set_attribute_typed(self, attr_name: str, typed_value: TypedValue) -> None:
        if not isinstance(typed_value, TypedValue):
            raise ValueError(
                f"Value for attribute '{attr_name}' of entity '{self.name}' "
                f"must be a TypedValue instance. Got type: {type(typed_value)}"
            )
        canonical_name = self._normalize_key(attr_name)
        self.attributes[canonical_name] = typed_value


    def remove_attribute(self, attr_name: str) -> None:
        canonical_name = self._normalize_key(attr_name)
        if canonical_name in self.attributes:
            del self.attributes[canonical_name]

    def has_attribute(self, attr_name: str) -> bool:
        canonical_name = self._normalize_key(attr_name)
        return canonical_name in self.attributes

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

    def is_attribute_dynamic(self, attr_name: str) -> bool:
        typed_value = self.attributes.get(attr_name)
        return typed_value.is_dynamic if typed_value else False

    def get_attribute_original_expression(self, attr_name: str) -> Optional[str]:
        typed_value = self.attributes.get(attr_name)
        return typed_value.original if typed_value and typed_value.is_dynamic else None

    def get_all_attributes_typed(self) -> Dict[str, TypedValue]:
        return self.attributes

    def get_identifier(self) -> str:
        """
        Returns a unique identifier string for this entity instance.
        Format: entity_type:category:name
        """
        # Ensure components are strings and handle potential None if necessary, though __post_init__ normalizes
        entity_type_str = str(self.entity_type).lower().strip()
        category_str = str(self.category).lower().strip() # Already normalized in __post_init__
        name_str = str(self.name).strip()
        return f"{entity_type_str}:{category_str}:{name_str}"

    def get_exclusive_resource_claims(self) -> List[str]:
        """
        Retrieves the list of exclusive resource claims for this entity.
        Returns an empty list if the attribute is not set, is None, or is not a list/string.
        """
        claims_tv = self.get_attribute_typed("exclusive_resource_claims")
        
        if not claims_tv or claims_tv.value is None:
            return [] # Default to no claims if attribute is missing or its value is None

        value = claims_tv.value
        if isinstance(value, list) and len(value) == 2 and value[0] == 'quote' and isinstance(value[1], list) and not value[1]:
            return []
        
        if isinstance(value, list):
            # Ensure all items in the list are strings
            if all(isinstance(item, str) for item in value):
                return value
            else:
                logger.warning(
                    f"Entity '{self.get_identifier()}' has 'exclusive_resource_claims' "
                    f"list with non-string items: {value}. Returning empty list."
                )
                return []
        elif isinstance(value, str):
            # If it's a single string, return it as a list with one item
            if value.strip(): # Avoid empty strings as claims
                return [value]
            else:
                return [] # Treat empty string claim as no claim
        
        logger.warning(
            f"Entity '{self.get_identifier()}' has 'exclusive_resource_claims' with unexpected "
            f"type: {type(value)}. Expected list of strings or a single string. Returning empty list."
        )
        return []

    def serialize(self) -> Dict[str, Any]:
        """
        Converts the Entity object into a JSON-serializable dictionary.
        This is suitable for API responses.
        """
        serialized_attributes = {
            attr_key: typed_value_obj.serialize()
            for attr_key, typed_value_obj in self.attributes.items()
        }
        return {
            "name": self.name,
            "entity_type": self.entity_type,
            "category": self.category,
            "attributes": serialized_attributes,
        }

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
