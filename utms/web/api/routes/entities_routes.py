# utms.web.api.routes.entities_routes.py

from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.responses import JSONResponse # Using JSONResponse directly

# Import the component
from utms.core.components.elements.time_entity import TimeEntityComponent
# Config for dependency injection
from utms.core.config import UTMSConfig 
from utms.web.dependencies import get_config # Assuming this returns UTMSConfig

# Pydantic models for API request/response if you define them (recommended for production)
# For now, we'll construct dicts directly for responses.
from utms.web.api.models.entities import EntityTypeDetailSchema # Already used for /types

# Import TypedValue to understand its structure for responses, but not directly manipulated here
# from utms.utms_types.field.types import TypedValue 

from utms.core.logger import get_logger

router = APIRouter()
logger = get_logger()

# Helper to get the TimeEntityComponent from the main UTMSConfig
def get_entities_component(main_config: UTMSConfig = Depends(get_config)) -> TimeEntityComponent:
    entities_component = main_config.get_component('entities')
    if not isinstance(entities_component, TimeEntityComponent):
        # This should ideally not happen if setup is correct
        logger.error("Entities component not found or is not of type TimeEntityComponent.")
        raise HTTPException(status_code=500, detail="Entities component not available.")
    if not entities_component._loaded: # Ensure component is loaded
        logger.info("Entities component not loaded, attempting to load now for API request.")
        try:
            entities_component.load()
        except Exception as e:
            logger.error(f"Failed to load entities component during API request: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to load entities data.")
    return entities_component


@router.get(
    "/api/entities/types", 
    response_model=List[EntityTypeDetailSchema], # Existing response model
    summary="Get all defined entity types with their schemas"
)
async def get_entity_types_with_details_api(
    entities_component: TimeEntityComponent = Depends(get_entities_component)
):
    try:
        # This component method should already return data in a suitable format
        details = entities_component.get_all_entity_type_details()
        return details
    except Exception as e:
        logger.error(f"Error fetching entity types: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error fetching entity types: {str(e)}")


@router.get("/api/entities", response_class=JSONResponse, summary="Get all entities or entities of a specific type")
async def get_all_or_typed_entities( # Renamed for clarity
    entity_type: Optional[str] = None, # e.g., "task", "event" (lowercase)
    entities_component: TimeEntityComponent = Depends(get_entities_component)
):
    try:
        entities_list = []
        if entity_type:
            entities_list = entities_component.get_by_type(entity_type.lower())
        else:
            # Get all entities of all types
            all_defined_types = entities_component.get_entity_types() # Returns list of lowercase type strings
            for et_key in all_defined_types:
                entities_list.extend(entities_component.get_by_type(et_key))
        
        # Convert TimeEntity objects (with TypedValue attributes) to JSON-serializable format
        api_response_list = []
        for entity_model_instance in entities_list:
            serialized_attributes = {}
            # entity_model_instance.attributes is Dict[str, TypedValue]
            for attr_key, typed_value_obj in entity_model_instance.get_all_attributes_typed().items():
                # TypedValue.serialize() returns a JSON-friendly dict for the attribute
                # e.g., {"value": ..., "type": ..., "is_dynamic": ..., "original": ...}
                serialized_attributes[attr_key] = typed_value_obj.serialize() 
            
            api_response_list.append({
                "name": entity_model_instance.name,
                "entity_type": entity_model_instance.entity_type, # e.g., "task"
                "attributes": serialized_attributes, 
            })
        
        return api_response_list
    except HTTPException: # Re-raise known HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error in get_all_or_typed_entities (type: {entity_type}): {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/api/entities/{entity_type}/{name}", response_class=JSONResponse, summary="Get a specific entity")
async def get_single_entity( # Renamed for clarity
    entity_type: str, # e.g., "task" (lowercase)
    name: str,
    entities_component: TimeEntityComponent = Depends(get_entities_component)
):
    try:
        entity_model_instance = entities_component.get_entity(entity_type.lower(), name)
        
        if not entity_model_instance:
            raise HTTPException(status_code=404, detail=f"Entity '{entity_type}:{name}' not found.")
        
        serialized_attributes = {}
        for attr_key, typed_value_obj in entity_model_instance.get_all_attributes_typed().items():
            serialized_attributes[attr_key] = typed_value_obj.serialize()
        
        return {
            "name": entity_model_instance.name,
            "entity_type": entity_model_instance.entity_type,
            "attributes": serialized_attributes,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching entity {entity_type}:{name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# For POST and PUT, define Pydantic models for request bodies for better validation.
# Example (simplified, place in your api/models/entities.py):
# class EntityAttributePayload(BaseModel):
#     value: Any
#     is_dynamic: Optional[bool] = False # If client wants to set/update a dynamic expression
#     original_expression: Optional[str] = None # The Hy code string
#     # Type might be provided by client, or inferred by component based on schema/value

# class CreateEntityPayload(BaseModel):
#     name: str
#     entity_type: str # lowercase
#     attributes: Optional[Dict[str, Any]] = {} # Raw values, component will create TypedValues

@router.post("/api/entities", response_class=JSONResponse, status_code=201, summary="Create a new entity")
async def create_new_entity( # Renamed
    # Using Body(embed=True) means payload should be like: {"entity_data": {"name": "...", ...}}
    # Simpler is often just the model itself as the body. For now, using Body fields.
    name: str = Body(..., embed=True, description="Unique name for the new entity"),
    entity_type: str = Body(..., embed=True, description="Type of the entity (e.g., 'task', lowercase)"),
    # attributes_raw are Python native values, or Hy code strings for dynamic 'code' fields
    attributes_raw: Dict[str, Any] = Body({}, embed=True, description="Attributes as raw Python values"),
    entities_component: TimeEntityComponent = Depends(get_entities_component)
):
    logger.debug(
        f"API create_new_entity: name='{name}', type='{entity_type}', attrs='{attributes_raw}'"
    )
    try:
        if entities_component.get_entity(entity_type.lower(), name):
            raise HTTPException(status_code=409, detail=f"Entity '{entity_type}:{name}' already exists.")
        
        # The component's create_entity method now handles converting raw attributes to TypedValues
        # based on schema and input.
        created_entity_model = entities_component.create_entity(
            name=name,
            entity_type=entity_type.lower(), # Ensure lowercase for consistency
            attributes_raw=attributes_raw 
        )
        
        # Serialize the created entity for the response
        serialized_attrs = {
            k: tv.serialize() for k, tv in created_entity_model.get_all_attributes_typed().items()
        }
        return {
            "name": created_entity_model.name,
            "entity_type": created_entity_model.entity_type,
            "attributes": serialized_attrs
        }
    except HTTPException:
        raise
    except ValueError as ve: # Catch specific errors from component/manager
        logger.warning(f"ValueError during entity creation: {ve}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error creating entity {entity_type}:{name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.put("/api/entities/{entity_type}/{name}/attributes/{attr_name}", response_class=JSONResponse, summary="Update an entity attribute")
async def update_single_entity_attribute( # Renamed
    entity_type: str, # lowercase
    name: str,
    attr_name: str,
    # For the body, it's better to use a Pydantic model to define the payload structure
    # e.g. value: Any, is_dynamic: bool = False, original_expression: Optional[str] = None
    # Using individual Body fields for now:
    new_value: Any = Body(..., alias="value", description="The new value for the attribute"),
    is_dynamic: bool = Body(False, description="Is this new value a dynamic Hy expression?"),
    original_expression: Optional[str] = Body(None, description="The Hy s-expression string if dynamic"),
    entities_component: TimeEntityComponent = Depends(get_entities_component)
):
    logger.debug(
        f"API update_single_entity_attribute: {entity_type}:{name}.{attr_name} "
        f"to value='{new_value}', is_dynamic={is_dynamic}, original='{original_expression}'"
    )
    try:
        # The component's update_entity_attribute handles TypedValue creation/update logic
        entities_component.update_entity_attribute(
            entity_type=entity_type.lower(),
            name=name,
            attr_name=attr_name,
            new_raw_value=new_value, # Pass the raw value from API
            is_new_value_dynamic=is_dynamic,
            new_original_expression=original_expression
        )
        
        # Fetch the updated entity to return its state
        updated_entity_model = entities_component.get_entity(entity_type.lower(), name)
        if not updated_entity_model: # Should not happen if update didn't error
            logger.error(f"Entity {entity_type}:{name} not found after presumed successful update.")
            raise HTTPException(status_code=500, detail="Failed to retrieve entity after update.")

        updated_typed_value = updated_entity_model.get_attribute_typed(attr_name)
        if not updated_typed_value:
             logger.error(f"Attribute {attr_name} not found on entity {entity_type}:{name} after update.")
             raise HTTPException(status_code=500, detail=f"Attribute {attr_name} missing post-update.")

        return {
            "entity_name": name,
            "entity_type": entity_type.lower(),
            "attribute_name": attr_name,
            "updated_attribute": updated_typed_value.serialize() # Return serialized TypedValue
        }
    except HTTPException:
        raise
    except ValueError as ve: # Catch specific errors like "entity not found"
        logger.warning(f"ValueError during attribute update: {ve}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error updating attribute {entity_type}:{name}.{attr_name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/api/entities/{entity_type}/{name}", status_code=204, summary="Delete an entity")
async def delete_single_entity( # Renamed
    entity_type: str, # lowercase
    name: str,
    entities_component: TimeEntityComponent = Depends(get_entities_component)
):
    try:
        # Check if entity exists before attempting deletion for a more specific response
        if not entities_component.get_entity(entity_type.lower(), name):
            raise HTTPException(status_code=404, detail=f"Entity '{entity_type}:{name}' not found for deletion.")
            
        entities_component.remove_entity(entity_type.lower(), name)
        # For 204, typically no content is returned.
        # If you need to return a JSON message, change status_code to 200.
        # return {"status": "success", "message": f"Entity {entity_type}:{name} deleted."}
        return None 
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting entity {entity_type}:{name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.put("/api/entities/{entity_type}/{name}/rename", response_class=JSONResponse, summary="Rename an entity")
async def rename_single_entity( # Renamed
    entity_type: str, # lowercase
    name: str, # current name
    new_name: str = Body(..., embed=True, description="The new unique name for the entity"),
    entities_component: TimeEntityComponent = Depends(get_entities_component)
):
    logger.debug(f"API rename_single_entity: type='{entity_type}', old_name='{name}', new_name='{new_name}'")
    try:
        # Component method handles checks for old_name existence and new_name conflict
        entities_component.rename_entity(entity_type.lower(), name, new_name)
        
        return {
            "status": "success",
            "message": f"Entity '{entity_type}:{name}' renamed to '{entity_type}:{new_name}'.",
            "old_name": name,
            "new_name": new_name,
            "entity_type": entity_type.lower()
        }
    except HTTPException:
        raise
    except ValueError as ve: # From component if old_name not found or new_name exists
        logger.warning(f"ValueError during entity rename: {ve}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(ve)) # Or 404/409 depending on error
    except Exception as e:
        logger.error(f"Error renaming entity {entity_type}:{name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


