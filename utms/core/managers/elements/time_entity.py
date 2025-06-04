# utms.core.managers.elements.time_entity.py
from typing import Any, Dict, List, Optional, Union

from utms.core.managers.base import BaseManager
from utms.core.models.elements.time_entity import TimeEntity  # Updated TimeEntity
from utms.utms_types import TimeEntityManagerProtocol
from utms.utms_types.field.types import TypedValue  # For deserialize


class TimeEntityManager(BaseManager[TimeEntity], TimeEntityManagerProtocol):
    """Manages time entities, now with category awareness."""

    def create(
        self,
        name: str,
        entity_type: str = "generic",
        attributes: Optional[Dict[str, TypedValue]] = None,  # Expects Dict[str, TypedValue]
        category: str = "default",  # New category parameter
    ) -> TimeEntity:
        """
        Create a new time entity.
        'attributes' should be a dictionary of already processed TypedValue objects.
        """
        entity_type_key = entity_type.lower()
        category_key = category.strip().lower() if category and category.strip() else "default"

        # Keying Strategy:
        # Option 1: Name is unique across all categories for a type. Key: f"{entity_type_key}:{name}"
        # Option 2: Name is unique only within a category for a type. Key: f"{entity_type_key}:{category_key}:{name}"
        # Let's stick with Option 1 for now for minimal changes to getters, assuming names are globally unique per type.
        # If Option 2 is desired, get_by_name_and_type would need 'category' param.
        generated_key = f"{entity_type_key}:{name}"

        if generated_key in self._items:
            self.logger.info(
                f"Entity '{generated_key}' already exists. It will be replaced (updated)."
            )
            self.remove(generated_key)

        entity = TimeEntity(
            name=name,
            entity_type=entity_type_key,
            category=category_key,  # Pass category to constructor
            attributes=attributes or {},
        )

        self.add(generated_key, entity)
        self.logger.debug(
            f"Created/Updated TimeEntity '{generated_key}' in category '{category_key}': {repr(entity)}"
        )
        return entity

    def get_by_name_and_type(self, name: str, entity_type: str) -> Optional[TimeEntity]:
        """Get a time entity by name and type (assumes name is unique across categories for this type)."""
        key = f"{entity_type.lower()}:{name}"
        return self.get(key)

    def get_by_type(self, entity_type: str, category: Optional[str] = None) -> List[TimeEntity]:
        """
        Get all time entities of a specific type.
        Optionally filters by category. If category is None, returns all for that type.
        """
        entity_type_key = entity_type.lower()
        entities_of_type = [
            entity for entity in self._items.values() if entity.entity_type == entity_type_key
        ]
        if category:
            category_key = category.strip().lower()
            return [entity for entity in entities_of_type if entity.category == category_key]
        return entities_of_type

    def get_by_attribute(
        self,
        attr_name: str,
        attr_value_to_match: Any,
        entity_type: Optional[str] = None,
        category: Optional[str] = None,
    ) -> List[TimeEntity]:
        """
        Get time entities with a specific attribute value.
        Optionally filters by entity_type and category.
        """
        results = []
        for entity in self._items.values():
            type_match = not entity_type or entity.entity_type == entity_type.lower()
            category_match = not category or entity.category == category.strip().lower()
            attr_match = (
                entity.has_attribute(attr_name)
                and entity.get_attribute_value(attr_name) == attr_value_to_match
            )

            if type_match and category_match and attr_match:
                results.append(entity)
        return results

    def get_by_dynamic_attribute_status(
        self,
        attr_name: str,
        is_dynamic: bool,
        entity_type: Optional[str] = None,
        category: Optional[str] = None,
    ) -> List[TimeEntity]:
        """
        Get time entities filtered by dynamic status of a specific attribute.
        Optionally filters by entity_type and category.
        """
        results = []
        for entity in self._items.values():
            type_match = not entity_type or entity.entity_type == entity_type.lower()
            category_match = not category or entity.category == category.strip().lower()
            dynamic_match = (
                entity.has_attribute(attr_name)
                and entity.is_attribute_dynamic(attr_name) == is_dynamic
            )

            if type_match and category_match and dynamic_match:
                results.append(entity)
        return results

    def get_categories_for_entity_type(self, entity_type: str) -> List[str]:
        """Gets all unique category names for a given entity type."""
        entity_type_key = entity_type.lower()
        categories = set()
        for entity in self._items.values():
            if entity.entity_type == entity_type_key:
                categories.add(entity.category)
        return sorted(list(categories))

    def serialize(self) -> Dict[str, Dict[str, Any]]:
        """Convert all managed time entities to a serializable dictionary format."""
        serialized_data: Dict[str, Dict[str, Any]] = {}
        for key, entity_instance in self._items.items():
            serialized_attributes: Dict[str, Any] = {}
            if entity_instance.attributes:
                for attr_key, typed_value_obj in entity_instance.attributes.items():
                    serialized_attributes[attr_key] = typed_value_obj.serialize()

            serialized_data[key] = {
                "name": entity_instance.name,
                "entity_type": entity_instance.entity_type,
                "category": entity_instance.category,  # Add category to serialization
                "attributes": serialized_attributes,
            }
        return serialized_data

    def deserialize(self, data: Dict[str, Dict[str, Any]]) -> None:
        """Load time entities from a serialized dictionary format."""
        self.clear()
        for key, entity_data_dict in data.items():  # key here is the old f"{type}:{name}"
            name = entity_data_dict["name"]
            entity_type = entity_data_dict["entity_type"]
            # Get category, default if not present for backward compatibility
            category = entity_data_dict.get("category", "default")

            serialized_attributes_data = entity_data_dict.get("attributes", {})
            final_attributes_for_model: Dict[str, TypedValue] = {}
            if isinstance(serialized_attributes_data, dict):
                for attr_key, serialized_typed_value_data in serialized_attributes_data.items():
                    try:
                        rehydrated_typed_value = TypedValue.deserialize(serialized_typed_value_data)
                        final_attributes_for_model[attr_key] = rehydrated_typed_value
                    except Exception as e:
                        self.logger.error(
                            f"Error deserializing TypedValue for attribute '{attr_key}' "
                            f"in entity '{key}' (name: {name}): {e}. Data: {serialized_typed_value_data}",
                            exc_info=True,
                        )
                        continue

            # Call self.create, which now accepts category
            self.create(
                name=name,
                entity_type=entity_type,
                category=category,
                attributes=final_attributes_for_model,
            )
        self.logger.info(f"Deserialized {len(self._items)} time entities into manager.")
