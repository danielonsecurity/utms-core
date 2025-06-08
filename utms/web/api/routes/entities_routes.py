from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, Body, Depends, HTTPException, Query  # Added Query
from fastapi.responses import JSONResponse

from utms.core.components.elements.entity import EntityComponent
from utms.core.config import UTMSConfig
from utms.core.logger import get_logger
from utms.utils import sanitize_filename
from utms.web.api.models.entities import (  # Add new Pydantic models for category payloads if desired, or use Body fields
    AttributeUpdatePayload,
    EndOccurrencePayload,
    EntityTypeDetailSchema,
)
from utms.web.dependencies import get_config

router = APIRouter()
logger = get_logger()


# Helper to get EntityComponent (remains the same)
def get_entities_component(main_config: UTMSConfig = Depends(get_config)) -> EntityComponent:
    entities_component = main_config.get_component("entities")
    if not isinstance(entities_component, EntityComponent):
        logger.error("Entities component not found or is not of type EntityComponent.")
        raise HTTPException(status_code=500, detail="Entities component not available.")
    if not entities_component._loaded:
        logger.info("Entities component not loaded, attempting to load now for API request.")
        try:
            entities_component.load()
        except Exception as e:
            logger.error(
                f"Failed to load entities component during API request: {e}", exc_info=True
            )
            raise HTTPException(status_code=500, detail="Failed to load entities data.")
    return entities_component


# --- Entity Type Schema Routes ---
@router.get(
    "/api/entities/types",
    response_model=List[EntityTypeDetailSchema],
    summary="Get all defined entity types with their schemas",
)
async def get_entity_types_with_details_api(
    entities_component: EntityComponent = Depends(get_entities_component),
):
    # ... (remains the same as response #13)
    try:
        details = entities_component.get_all_entity_type_details()
        return details
    except Exception as e:
        logger.error(f"Error fetching entity types: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# --- Entity Instance Routes ---
@router.get(
    "/api/entities",
    response_class=JSONResponse,
    summary="Get entities, optionally filtered by type and category",
)
async def get_entities_api(  # Renamed for clarity
    entity_type: Optional[str] = Query(None, description="e.g., 'task', 'event' (lowercase)"),
    category: Optional[str] = Query(
        None, description="e.g., 'work', 'personal', 'default' (lowercase)"
    ),
    entities_component: EntityComponent = Depends(get_entities_component),
):
    try:
        entities_list = []
        if entity_type:
            # Component's get_by_type now accepts an optional category
            entities_list = entities_component.get_by_type(
                entity_type.lower(), category.lower() if category else None
            )
        elif category:
            # If only category is specified, get all entities from that category across all types
            # This might require a new component method or iteration here.
            # For now, let's assume if category is given, entity_type must also be given.
            # Or, to implement "all entities in a category":
            all_types = entities_component.get_entity_types()
            for et_key in all_types:
                entities_list.extend(entities_component.get_by_type(et_key, category.lower()))
            logger.info(
                f"Fetched all entities for category '{category}' across {len(all_types)} types."
            )
        else:
            # Get all entities of all types from all categories
            all_defined_types = entities_component.get_entity_types()
            for et_key in all_defined_types:
                entities_list.extend(
                    entities_component.get_by_type(et_key, None)
                )  # Get all categories for this type

        api_response_list = []
        for entity_model_instance in entities_list:
            serialized_attributes = {
                attr_key: typed_value_obj.serialize()
                for attr_key, typed_value_obj in entity_model_instance.get_all_attributes_typed().items()
            }
            api_response_list.append(
                {
                    "name": entity_model_instance.name,
                    "entity_type": entity_model_instance.entity_type,
                    "category": entity_model_instance.category,  # Include category in response
                    "attributes": serialized_attributes,
                }
            )
        return api_response_list
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error in get_entities_api (type: {entity_type}, cat: {category}): {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/api/entities/types/{entity_type_key}/categories",
    response_model=List[str],
    summary="List categories for an entity type",
)
async def list_entity_categories_api(
    entity_type_key: str,
    entities_component: EntityComponent = Depends(get_entities_component),
):
    try:
        if not entities_component.entity_types.get(
            entity_type_key.lower()
        ):  # Check against lowercase
            logger.warning(
                f"Category listing: Entity type '{entity_type_key}' not found in component schemas."
            )
            raise HTTPException(
                status_code=404, detail=f"Entity type '{entity_type_key}' not defined."
            )
        categories = entities_component.get_categories(entity_type_key.lower())  # Pass lowercase
        return categories
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing categories for type '{entity_type_key}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/api/entities/{entity_type}/{category}/{name}",
    response_class=JSONResponse,
    summary="Get a specific entity by type and name",
)
async def get_single_entity_api(
    entity_type: str,
    category: str,
    name: str,
    entities_component: EntityComponent = Depends(get_entities_component),
):
    try:
        # Component's get_entity assumes name is unique per type. If not, it needs category.
        entity_model_instance = entities_component.get_entity(
            entity_type.lower(), category.lower(), name
        )
        if not entity_model_instance:
            raise HTTPException(
                status_code=404, detail=f"Entity '{entity_type}:{category}:{name}' not found."
            )

        serialized_attributes = {
            k: tv.serialize() for k, tv in entity_model_instance.get_all_attributes_typed().items()
        }
        return {
            "name": entity_model_instance.name,
            "entity_type": entity_model_instance.entity_type,
            "category": entity_model_instance.category,
            "attributes": serialized_attributes,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching entity {entity_type}:{category}:{name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post(
    "/api/entities", response_class=JSONResponse, status_code=201, summary="Create a new entity"
)
async def create_new_entity_api(
    name: str = Body(..., embed=True),
    entity_type: str = Body(..., embed=True),
    category: Optional[str] = Body(
        "default", embed=True, description="Category for the new entity (lowercase)"
    ),
    attributes_raw: Dict[str, Any] = Body(default_factory=dict, embed=True),
    entities_component: EntityComponent = Depends(get_entities_component),
):
    logger.debug(
        f"API create_new_entity: name='{name}', type='{entity_type}', category='{category}', attrs='{attributes_raw}'"
    )
    try:
        category_key = category.lower() if category else "default"
        # get_entity checks across all categories if name is assumed unique per type
        if entities_component.get_entity(entity_type.lower(), category_key, name):
            raise HTTPException(
                status_code=409,
                detail=f"Entity '{entity_type}:{name}' already exists (name must be unique for this type).",
            )

        # Component's create_entity now accepts category
        created_entity_model = entities_component.create_entity(
            name=name,
            entity_type=entity_type.lower(),
            category=category.lower() if category else "default",
            attributes_raw=attributes_raw,
        )

        serialized_attrs = {
            k: tv.serialize() for k, tv in created_entity_model.get_all_attributes_typed().items()
        }
        return {
            "name": created_entity_model.name,
            "entity_type": created_entity_model.entity_type,
            "category": created_entity_model.category,  # Include category
            "attributes": serialized_attrs,
        }
    # ... (exception handling same as response #13) ...
    except HTTPException:
        raise
    except ValueError as ve:
        logger.warning(f"ValueError: {ve}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error creating entity: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/api/entities/{entity_type}/{category}/{name}/attributes/{attr_name}",
    response_class=JSONResponse,
    summary="Update an entity attribute",
)
async def update_entity_attribute_api(  # Renamed for clarity
    entity_type: str,
    category: str,
    name: str,
    attr_name: str,
    payload: AttributeUpdatePayload,
    entities_component: EntityComponent = Depends(get_entities_component),
):
    logger.debug(
        f"API update_entity_attribute: {entity_type}:{category}:{name}.{attr_name} with payload: {payload.model_dump(mode='json')}"
    )
    try:
        entities_component.update_entity_attribute(
            entity_type=entity_type.lower(),
            category=category.lower(),
            name=name,
            attr_name=attr_name,
            new_raw_value_from_api=payload.value,
            is_new_value_dynamic=payload.is_dynamic,
            new_original_expression=payload.original,
        )
        updated_entity_model = entities_component.get_entity(
            entity_type.lower(), category.lower(), name
        )
        if not updated_entity_model:
            raise HTTPException(status_code=500, detail="Entity vanished after update.")
        updated_typed_value = updated_entity_model.get_attribute_typed(attr_name)
        if not updated_typed_value:
            raise HTTPException(status_code=500, detail="Attribute vanished after update.")
        return {
            "entity_name": name,
            "entity_type": entity_type.lower(),
            "category": updated_entity_model.category,
            "attribute_name": attr_name,
            "updated_attribute": updated_typed_value.serialize(),
        }
    except HTTPException:
        raise
    except ValueError as ve:
        logger.warning(
            f"ValueError during attribute update for {entity_type}:{category}:{name}.{attr_name}: {ve}",
            exc_info=True,
        )
        detail_str = str(ve).lower()
        status_code = 404 if "not found" in detail_str or "no such entity" in detail_str else 400
        raise HTTPException(status_code=status_code, detail=str(ve))
    except Exception as e:
        logger.error(
            f"Error updating attr for {entity_type}:{category}:{name}.{attr_name}: {e}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/api/entities/{entity_type}/{name}/category",
    response_class=JSONResponse,
    summary="Move an entity to a new category",
)
async def move_entity_category_api(
    entity_type: str,
    name: str,
    new_category: str = Body(..., embed=True, description="The new category name (lowercase)"),
    entities_component: EntityComponent = Depends(get_entities_component),
):
    logger.debug(
        f"API move_entity_category: Moving '{entity_type}:{name}' to category '{new_category}'"
    )
    try:
        success = entities_component.move_entity_to_category(
            entity_type.lower(), name, new_category.lower()
        )
        if not success:
            # More specific error might have been raised by component, or just generic failure
            raise HTTPException(
                status_code=400,
                detail="Failed to move entity to new category. Entity may not exist or new category is invalid.",
            )

        moved_entity = entities_component.get_entity(entity_type.lower(), name)
        if not moved_entity or moved_entity.category != new_category.lower():
            raise HTTPException(
                status_code=500, detail="Entity move reported success but verification failed."
            )

        return {
            "message": f"Entity '{entity_type}:{name}' moved to category '{new_category}'.",
            "name": moved_entity.name,
            "entity_type": moved_entity.entity_type,
            "new_category": moved_entity.category,
        }
    except HTTPException:
        raise
    except ValueError as ve:
        logger.warning(f"ValueError: {ve}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error moving entity category: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/api/entities/{entity_type}/{category}/{name}", status_code=204, summary="Delete an entity"
)
async def delete_entity_api(  # Renamed
    entity_type: str,
    category: str,
    name: str,
    entities_component: EntityComponent = Depends(get_entities_component),
):
    # ... (remains same as response #13) ...
    try:
        if not entities_component.get_entity(entity_type.lower(), category.lower(), name):
            raise HTTPException(
                status_code=404, detail=f"Entity '{entity_type}:{category}:{name}' not found."
            )
        entities_component.remove_entity(entity_type.lower(), category.lower(), name)
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting entity {entity_type}:{category}:{name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/api/entities/{entity_type}/{old_category}/{name}/rename",
    response_class=JSONResponse,
    summary="Rename an entity",
)
async def rename_entity_api(
    entity_type: str,
    old_category: str,
    old_name: str,
    new_name: str = Body(..., embed=True),
    new_category: Optional[str] = Body(
        None, embed=True, description="Optional new category (lowercase)"
    ),
    entities_component: EntityComponent = Depends(get_entities_component),
):
    logger.debug(
        f"API rename_entity: type='{entity_type}', old_cat='{old_category}', old_name='{old_name}', "
        f"new_name='{new_name}', new_cat='{new_category}'"
    )
    try:
        entities_component.rename_entity(
            entity_type_key=entity_type.lower(),
            old_category_key=old_category.lower(),
            old_name_key=old_name,
            new_name_key=new_name,
            new_category_key=new_category.lower() if new_category else None,
        )
        final_category = new_category.lower() if new_category else old_category.lower()
        renamed_entity_model = entities_component.get_entity(
            entity_type.lower(), final_category, new_name
        )
        if not renamed_entity_model:
            raise HTTPException(status_code=500, detail="Entity vanished after rename operation.")

        return {
            "status": "success",
            "message": f"Entity renamed/moved.",
            "old_identifier": f"{entity_type.lower()}:{old_category.lower()}:{old_name}",
            "new_identifier": f"{renamed_entity_model.entity_type}:{renamed_entity_model.category}:{renamed_entity_model.name}",
            "entity": {  # Optionally return the full new entity
                "name": renamed_entity_model.name,
                "entity_type": renamed_entity_model.entity_type,
                "category": renamed_entity_model.category,
            },
        }
    except HTTPException:
        raise
    except ValueError as ve:
        logger.warning(
            f"ValueError during rename for {entity_type}:{old_category}:{old_name}: {ve}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=400 if "not found" not in str(ve).lower() else 404, detail=str(ve)
        )
    except Exception as e:
        logger.error(
            f"Error renaming entity {entity_type}:{old_category}:{old_name}: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/api/entities/types/{entity_type_key}/categories",
    status_code=201,
    summary="Create a new category for an entity type",
)
async def create_entity_category_api(
    entity_type_key: str,  # lowercase
    category_name: str = Body(..., embed=True, description="Name for the new category"),
    entities_component: EntityComponent = Depends(get_entities_component),
):
    logger.debug(
        f"API create_entity_category: type='{entity_type_key}', new_category='{category_name}'"
    )
    try:
        if not entities_component.entity_types.get(entity_type_key.lower()):
            raise HTTPException(
                status_code=404, detail=f"Entity type '{entity_type_key}' not found."
            )

        success = entities_component.create_category(entity_type_key.lower(), category_name)
        if not success:
            # Check if it's because it already exists
            existing_categories = entities_component.get_categories(entity_type_key.lower())
            if sanitize_filename(category_name.lower()) in [
                sanitize_filename(c) for c in existing_categories
            ]:
                raise HTTPException(
                    status_code=409,
                    detail=f"Category '{category_name}' already exists for type '{entity_type_key}'.",
                )
            raise HTTPException(status_code=400, detail="Failed to create category.")
        return {
            "message": f"Category '{category_name}' created successfully for type '{entity_type_key}'.",
            "category_name": sanitize_filename(category_name.lower()),
        }
    except HTTPException:
        raise
    except ValueError as ve:
        logger.warning(f"ValueError: {ve}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error creating category: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/api/entities/types/{entity_type_key}/categories/{category_name}",
    summary="Rename a category for an entity type",
)
async def rename_entity_category_api(
    entity_type_key: str,  # lowercase
    category_name: str,  # current category name (lowercase, sanitized form from URL)
    new_category_name: str = Body(..., embed=True, description="New name for the category"),
    entities_component: EntityComponent = Depends(get_entities_component),
):
    logger.debug(
        f"API rename_entity_category: type='{entity_type_key}', old='{category_name}', new='{new_category_name}'"
    )
    try:
        if not entities_component.entity_types.get(entity_type_key.lower()):
            raise HTTPException(
                status_code=404, detail=f"Entity type '{entity_type_key}' not found."
            )

        success = entities_component.rename_category(
            entity_type_key.lower(), category_name, new_category_name
        )
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Failed to rename category. Check if old name exists or new name is valid/available.",
            )
        return {
            "message": f"Category '{category_name}' renamed to '{new_category_name}' for type '{entity_type_key}'.",
            "old_name": category_name,
            "new_name": sanitize_filename(new_category_name.lower()),
        }
    except HTTPException:
        raise
    except ValueError as ve:
        logger.warning(f"ValueError: {ve}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error renaming category: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/api/entities/types/{entity_type_key}/categories/{category_name}",
    status_code=204,
    summary="Delete a category for an entity type",
)
async def delete_entity_category_api(
    entity_type_key: str,  # lowercase
    category_name: str,  # category name to delete (lowercase, sanitized form from URL)
    move_entities_to_default: bool = Query(
        True, description="Move entities to 'default' category instead of deleting them."
    ),
    entities_component: EntityComponent = Depends(get_entities_component),
):
    logger.debug(
        f"API delete_entity_category: type='{entity_type_key}', category='{category_name}', move_to_default={move_entities_to_default}"
    )
    try:
        if not entities_component.entity_types.get(entity_type_key.lower()):
            raise HTTPException(
                status_code=404, detail=f"Entity type '{entity_type_key}' not found."
            )
        if category_name.lower() == "default":
            raise HTTPException(status_code=400, detail="Cannot delete the 'default' category.")

        success = entities_component.delete_category(
            entity_type_key.lower(), category_name, move_entities_to_default
        )
        if not success:  # Could be "not found" or other failure
            # Check if it was "not found" vs actual error
            current_categories = entities_component.get_categories(entity_type_key.lower())
            if sanitize_filename(category_name.lower()) not in current_categories:
                raise HTTPException(
                    status_code=404,
                    detail=f"Category '{category_name}' not found for type '{entity_type_key}'.",
                )
            raise HTTPException(status_code=500, detail="Failed to delete category.")
        return None
    except HTTPException:
        raise
    except ValueError as ve:
        logger.warning(f"ValueError: {ve}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error deleting category: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/api/entities/{entity_type}/{category}/{name}/occurrences/start",
    response_class=JSONResponse,
    summary="Start a new occurrence for an entity",
    status_code=200,
)
async def start_entity_occurrence_api(
    entity_type: str,
    category: str,
    name: str,
    entities_component: EntityComponent = Depends(get_entities_component),
):
    """
    Starts a new timed occurrence for a given entity.
    This sets the 'active_occurrence_start_time' attribute to the current time.
    """
    try:
        updated_entity = entities_component.start_occurrence(
            entity_type=entity_type,
            category=category,
            name=name,
        )
        return updated_entity.serialize()
    except (ValueError, TypeError) as e:
        # 404 if entity not found, 409 if already started, 400 for other value errors
        detail_str = str(e).lower()
        if "not found" in detail_str:
            status_code = 404
        elif "already in progress" in detail_str:
            status_code = 409  # Conflict
        else:
            status_code = 400  # Bad Request
        raise HTTPException(status_code=status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Error starting occurrence for {entity_type}:{name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal server error occurred.")


@router.post(
    "/api/entities/{entity_type}/{category}/{name}/occurrences/end",
    response_class=JSONResponse,
    summary="End an in-progress occurrence for an entity",
    status_code=200,
)
async def end_entity_occurrence_api(
    entity_type: str,
    category: str,
    name: str,
    payload: EndOccurrencePayload,
    entities_component: EntityComponent = Depends(get_entities_component),
):
    """
    Ends an in-progress timed occurrence. This creates a new entry in the
    'occurrences' list and clears the 'active_occurrence_start_time'.
    """
    try:
        updated_entity = entities_component.end_occurrence(
            entity_type=entity_type,
            category=category,
            name=name,
            notes=payload.notes,
            metadata=payload.metadata,
        )
        return updated_entity.serialize()
    except (ValueError, TypeError) as e:
        # 404 if entity not found, 409 if not started, 400 for other value errors
        detail_str = str(e).lower()
        if "not found" in detail_str:
            status_code = 404
        elif "no active occurrence" in detail_str:
            status_code = 409  # Conflict
        else:
            status_code = 400  # Bad Request
        raise HTTPException(status_code=status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Error ending occurrence for {entity_type}:{name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal server error occurred.")
