from typing import Any, Dict, List, Optional, Union

from utms.core.managers.base import BaseManager
from utms.core.models import TimeEntity
from utms.utms_types import TimeEntityManagerProtocol


class TimeEntityManager(BaseManager[TimeEntity], TimeEntityManagerProtocol):
    """Manages time entities with their properties and relationships."""

    def create(
        self,
        name: str,
        entity_type: str = "generic",
        attributes: Optional[Dict[str, Any]] = None,
        dynamic_fields: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> TimeEntity:
        """Create a new time entity."""
        # Generate a unique key for the entity
        key = f"{entity_type}:{name}"
        
        if key in self._items:
            # If entity exists, update it instead of raising an error
            self.remove(key)
            
        # Create the time entity with attributes and dynamic fields
        entity = TimeEntity(
            name=name,
            entity_type=entity_type,
            attributes=attributes or {},
            dynamic_fields=dynamic_fields or {},
        )

        self.add(key, entity)
        return entity

    def get_by_name_and_type(self, name: str, entity_type: str) -> Optional[TimeEntity]:
        """Get a time entity by name and type."""
        key = f"{entity_type}:{name}"
        return self.get(key)

    def get_by_type(self, entity_type: str) -> List[TimeEntity]:
        """Get all time entities of a specific type."""
        return [
            entity for entity in self._items.values() 
            if entity.entity_type == entity_type
        ]

    def get_by_attribute(self, attr_name: str, attr_value: Any) -> List[TimeEntity]:
        """Get time entities with a specific attribute value."""
        return [
            entity for entity in self._items.values() 
            if entity.has_attribute(attr_name) and entity.get_attribute(attr_name) == attr_value
        ]

    def get_by_dynamic_field(self, field_name: str, is_dynamic: bool) -> List[TimeEntity]:
        """Get time entities filtered by dynamic status of a specific field."""
        return [
            entity for entity in self._items.values() 
            if entity.is_field_dynamic(field_name) == is_dynamic
        ]

    def serialize(self) -> Dict[str, Dict[str, Any]]:
        """Convert time entities to serializable format."""
        return {
            key: {
                "name": entity.name,
                "entity_type": entity.entity_type,
                "attributes": entity.attributes,
                "dynamic_fields": entity.dynamic_fields,
            }
            for key, entity in self._items.items()
        }

    def deserialize(self, data: Dict[str, Dict[str, Any]]) -> None:
        """Load time entities from serialized data."""
        self.clear()
        for key, entity_data in data.items():
            self.create(
                name=entity_data["name"],
                entity_type=entity_data["entity_type"],
                attributes=entity_data.get("attributes", {}),
                dynamic_fields=entity_data.get("dynamic_fields", {}),
            )
