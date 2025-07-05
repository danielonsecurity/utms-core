from typing import Any, Dict, List, Optional, Union

from utms.core.managers.base import BaseManager
from utms.core.models.elements.entity import Entity
from utms.utms_types import EntityManagerProtocol
from utms.utms_types.field.types import TypedValue


class EntityManager(BaseManager[Entity], EntityManagerProtocol):  # Renamed
    """Manages entities, now with category-aware unique keys."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs) 
        self._claimed_resources: Dict[str, str] = {}

    def _generate_key(self, entity_type: str, category: str, name: str) -> str:
        """Helper to generate the consistent composite key."""
        return f"{entity_type.lower().strip()}:{category.lower().strip()}:{name.strip()}"

    def clear(self):
        super().clear() 
        self._claimed_resources.clear()
        self.logger.debug("Cleared all entities and resource claims from EntityManager.")

    def create(
        self,
        name: str,
        entity_type: str,
        attributes: Optional[Dict[str, TypedValue]] = None,
        category: str = "default",
    ) -> Entity:
        entity_type_key = entity_type.lower().strip()
        category_key = category.strip().lower() if category and category.strip() else "default"
        name_key = name.strip() 

        if not name_key:
            self.logger.error("Entity name cannot be empty.")
            raise ValueError("Entity name cannot be empty.")
        if not entity_type_key:
            self.logger.error("Entity type cannot be empty.")
            raise ValueError("Entity type cannot be empty.")
        generated_key = self._generate_key(entity_type_key, category_key, name_key)

        if generated_key in self._items:
            self.logger.info(f"Entity '{generated_key}' already exists. It will be replaced.")
            existing_entity_to_replace = self._items.get(generated_key)
            if existing_entity_to_replace:
                self.release_claims(existing_entity_to_replace) 

        entity = Entity(
            name=name_key,
            entity_type=entity_type_key,
            category=category_key,
            attributes=attributes or {},
        )

        self.add(generated_key, entity)  # BaseManager.add takes key, item
        self.logger.debug(f"Created/Replaced Entity '{generated_key}': {repr(entity)}")
        return entity

    def get_all_entities(self) -> List[Entity]:
        """Returns a flat list of all managed entity instances."""
        return list(self._items.values())

    def get_by_name_type_category(
        self, name: str, entity_type: str, category: str
    ) -> Optional[Entity]:
        """Get an entity by its unique combination of name, type, and category."""
        key = self._generate_key(entity_type, category, name)
        return self.get(key)

    def remove_entity(self, name: str, entity_type: str, category: str) -> bool:
        """Remove an entity by its name, type, and category. Also releases its claims."""
        key = self._generate_key(entity_type, category, name)
        entity_to_remove = self.get(key) # Get the entity object before removing it

        if entity_to_remove:
            self.release_claims(entity_to_remove) # Release claims before removing
            self.remove(key)  # BaseManager.remove takes key
            self.logger.debug(f"Removed entity '{key}' and released its claims.")
            return True
        
        self.logger.warning(f"Entity '{key}' not found for removal.")
        return False

    def get_all_active_entities(self) -> List[Entity]:
        """Returns a list of all entities that currently have an active occurrence."""
        active_entities = []
        for entity in self._items.values():
            # Assuming 'active_occurrence_start_time' is the indicator
            # and its TypedValue.value will be a datetime object if active, or None if not.
            if entity.get_attribute_value("active_occurrence_start_time") is not None:
                active_entities.append(entity)
        return active_entities

    def register_claims(self, entity: Entity) -> None:
        """Registers the exclusive resource claims for the given entity."""
        entity_id = entity.get_identifier()
        claims = entity.get_exclusive_resource_claims()
        if not claims:
            return

        for resource in claims:
            if resource in self._claimed_resources:
                self.logger.error(
                    f"Attempted to register claim for resource '{resource}' by '{entity_id}', "
                    f"but it's already claimed by '{self._claimed_resources[resource]}'. "
                    "This indicates a logic error in conflict resolution."
                )
            self._claimed_resources[resource] = entity_id
            self.logger.debug(f"Entity '{entity_id}' claimed resource '{resource}'.")
        self.logger.debug(f"Current claims map: {self._claimed_resources}")


    def release_claims(self, entity: Entity) -> None:
        """Releases all exclusive resource claims held by the given entity."""
        entity_id = entity.get_identifier()
        claims_to_release = entity.get_exclusive_resource_claims() # Get what it *would* claim
        
        resources_held_by_entity = [
            res for res, holder_id in self._claimed_resources.items() if holder_id == entity_id
        ]

        if not resources_held_by_entity:
            return

        for resource in resources_held_by_entity:
            if self._claimed_resources.get(resource) == entity_id:
                del self._claimed_resources[resource]
                self.logger.debug(f"Entity '{entity_id}' released resource '{resource}'.")
            else:
                # This case should ideally not happen if logic is correct
                self.logger.warning(
                    f"Tried to release resource '{resource}' for entity '{entity_id}', "
                    f"but it was either not claimed or claimed by another entity: '{self._claimed_resources.get(resource)}'."
                )
        if resources_held_by_entity: # Log only if something was actually released
             self.logger.debug(f"Current claims map after release by {entity_id}: {self._claimed_resources}")


    def get_claiming_entity_id(self, resource: str) -> Optional[str]:
        """Returns the identifier of the entity currently claiming the given resource, or None."""
        return self._claimed_resources.get(resource)

    def get_by_type(self, entity_type: str, category: Optional[str] = None) -> List[Entity]:
        entity_type_key = entity_type.lower().strip()
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
    ) -> List[Entity]:
        """
        Get entities with a specific attribute value.
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
    ) -> List[Entity]:
        """
        Get entities filtered by dynamic status of a specific attribute.
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
        """Convert all managed entities to a serializable dictionary format.
        The top-level key in the returned dict is now the composite entity_type:category:name key.
        """
        serialized_data: Dict[str, Dict[str, Any]] = {}
        for composite_key, entity_instance in self._items.items():
            serialized_attributes: Dict[str, Any] = {}
            if entity_instance.attributes:
                for attr_key, typed_value_obj in entity_instance.attributes.items():
                    serialized_attributes[attr_key] = typed_value_obj.serialize()

            serialized_data[composite_key] = {  # Use composite_key from _items
                "name": entity_instance.name,
                "entity_type": entity_instance.entity_type,
                "category": entity_instance.category,
                "attributes": serialized_attributes,
            }
        return serialized_data

    def deserialize(self, data: Dict[str, Dict[str, Any]]) -> None:
        """Load entities from a serialized dictionary format.
        Assumes the top-level key in 'data' is the composite entity_type:category:name key.
        """
        self.clear()
        for composite_key, entity_data_dict in data.items():
            try:
                name = entity_data_dict["name"]
                entity_type = entity_data_dict["entity_type"]
                category = entity_data_dict.get("category", "default")  # Fallback for older data
                serialized_attributes_data = entity_data_dict.get("attributes", {})
                final_attributes_for_model: Dict[str, TypedValue] = {}
                if isinstance(serialized_attributes_data, dict):
                    for attr_key, serialized_typed_value_data in serialized_attributes_data.items():
                        final_attributes_for_model[attr_key] = TypedValue.deserialize(
                            serialized_typed_value_data
                        )
                self.create(
                    name=name,
                    entity_type=entity_type,
                    category=category,
                    attributes=final_attributes_for_model,
                )
            except Exception as e_main:
                self.logger.error(
                    f"Error deserializing entity for key '{composite_key}': {e_main}", exc_info=True
                )
                continue
        self.logger.info(f"Deserialized {len(self._items)} entities into manager.")
