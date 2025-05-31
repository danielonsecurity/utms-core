# utms.core.managers.elements.time_entity.py

from typing import Any, Dict, List, Optional, Union

from utms.core.managers.base import BaseManager
from utms.core.models.elements.time_entity import TimeEntity # Import the (soon to be) updated TimeEntity
from utms.utms_types import TimeEntityManagerProtocol
from utms.utms_types.field.types import TypedValue # Import TypedValue for type hinting and deserialize

class TimeEntityManager(BaseManager[TimeEntity], TimeEntityManagerProtocol):
    """Manages time entities, now expecting attributes as Dict[str, TypedValue]."""

    def create(
        self,
        name: str,
        entity_type: str = "generic",
        attributes: Optional[Dict[str, TypedValue]] = None, # Expects Dict[str, TypedValue]
        # dynamic_fields parameter is no longer needed as this info is in TypedValue
    ) -> TimeEntity:
        """
        Create a new time entity.
        The 'attributes' parameter should be a dictionary where values are TypedValue objects
        that have already been processed (e.g., dynamic expressions resolved) by the loader.
        """
        # Generate a unique key for the entity
        key = f"{entity_type}:{name}"
        
        if key in self._items:
            # If entity exists, remove old one to replace it (update behavior)
            self.logger.debug(f"Entity '{key}' already exists. Replacing it.")
            self.remove(key) # remove() is from BaseManager, just deletes from self._items
            
        # Create the time entity.
        # The TimeEntity constructor now expects 'attributes' to be Dict[str, TypedValue].
        entity = TimeEntity(
            name=name,
            entity_type=entity_type,
            attributes=attributes or {}, # Pass the Dict[str, TypedValue]
        )

        self.add(key, entity) # add() is from BaseManager
        self.logger.debug(f"Created/Updated TimeEntity '{key}': {repr(entity)}")
        return entity

    def get_by_name_and_type(self, name: str, entity_type: str) -> Optional[TimeEntity]:
        """Get a time entity by name and type."""
        key = f"{entity_type}:{name}"
        return self.get(key) # get() is from BaseManager

    def get_by_type(self, entity_type: str) -> List[TimeEntity]:
        """Get all time entities of a specific type."""
        return [
            entity for entity in self._items.values() 
            if entity.entity_type == entity_type
        ]

    def get_by_attribute(self, attr_name: str, attr_value_to_match: Any) -> List[TimeEntity]:
        """
        Get time entities where the resolved value of a specific attribute matches attr_value_to_match.
        """
        matched_entities = []
        for entity in self._items.values():
            # Use get_attribute_value to compare against the resolved Python value
            if entity.has_attribute(attr_name) and \
               entity.get_attribute_value(attr_name) == attr_value_to_match:
                matched_entities.append(entity)
        return matched_entities

    def get_by_dynamic_attribute_status(self, attr_name: str, is_dynamic: bool) -> List[TimeEntity]:
        """
        Get time entities filtered by the dynamic status of a specific attribute.
        Renamed from get_by_dynamic_field for clarity.
        """
        matched_entities = []
        for entity in self._items.values():
            if entity.has_attribute(attr_name) and \
               entity.is_attribute_dynamic(attr_name) == is_dynamic:
                matched_entities.append(entity)
        return matched_entities

    def serialize(self) -> Dict[str, Dict[str, Any]]:
        """Convert all managed time entities to a serializable dictionary format."""
        serialized_data: Dict[str, Dict[str, Any]] = {}
        for key, entity_instance in self._items.items():
            # entity_instance is a TimeEntity object
            serialized_attributes: Dict[str, Any] = {}
            if entity_instance.attributes:
                for attr_key, typed_value_obj in entity_instance.attributes.items():
                    # typed_value_obj is a TypedValue instance
                    # TypedValue.serialize() returns a JSON-friendly dict for the attribute
                    serialized_attributes[attr_key] = typed_value_obj.serialize() 
            
            serialized_data[key] = {
                "name": entity_instance.name,
                "entity_type": entity_instance.entity_type,
                "attributes": serialized_attributes, # This is now Dict[str, SerializedTypedValue]
                # "dynamic_fields" is no longer directly on the entity model
            }
        return serialized_data

    def deserialize(self, data: Dict[str, Dict[str, Any]]) -> None:
        """Load time entities from a serialized dictionary format."""
        self.clear() # Clear existing items
        for key, entity_data_dict in data.items():
            name = entity_data_dict["name"]
            entity_type = entity_data_dict["entity_type"]
            
            # This will be Dict[str, SerializedTypedValueData]
            serialized_attributes_data = entity_data_dict.get("attributes", {})
            
            final_attributes_for_model: Dict[str, TypedValue] = {}
            if isinstance(serialized_attributes_data, dict):
                for attr_key, serialized_typed_value_data in serialized_attributes_data.items():
                    # Reconstruct TypedValue object from its serialized form
                    try:
                        rehydrated_typed_value = TypedValue.deserialize(serialized_typed_value_data)
                        final_attributes_for_model[attr_key] = rehydrated_typed_value
                    except Exception as e:
                        self.logger.error(
                            f"Error deserializing TypedValue for attribute '{attr_key}' "
                            f"in entity '{key}': {e}. Data: {serialized_typed_value_data}",
                            exc_info=True
                        )
                        # Decide: skip attribute or fail? For now, skip.
                        continue
            
            # Call self.create, which now expects Dict[str, TypedValue] for attributes
            self.create(
                name=name,
                entity_type=entity_type,
                attributes=final_attributes_for_model,
            )
        self.logger.info(f"Deserialized {len(self._items)} time entities.")
