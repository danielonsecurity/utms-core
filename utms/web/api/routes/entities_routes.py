from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

from utms.core.config import UTMSConfig as Config
from utms.core.hy import evaluate_hy_expression
from utms.core.services.dynamic import dynamic_resolution_service
from utms.web.dependencies import get_config

router = APIRouter()

# Get all entities or entities of a specific type
@router.get("/api/entities", response_class=JSONResponse)
async def get_entities(
    entity_type: Optional[str] = None,
    config: Config = Depends(get_config)
):
    try:
        entities_component = config.get_component('entities')
        
        # Get all entities or filter by type
        if entity_type:
            entities_list = entities_component.get_by_type(entity_type)
        else:
            entities_list = []
            for entity_type in entities_component.get_entity_types():
                entities_list.extend(entities_component.get_by_type(entity_type))
        
        # Convert entities to JSON-serializable format
        result = []
        for entity in entities_list:
            result.append({
                "name": entity.name,
                "entity_type": entity.entity_type,
                "attributes": entity.attributes,
                "dynamic_fields": {
                    field: {
                        "original": info.get("original"),
                        "value": info.get("value")
                    } for field, info in entity.dynamic_fields.items()
                }
            })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Get entity types
@router.get("/api/entities/types", response_class=JSONResponse)
async def get_entity_types(config: Config = Depends(get_config)):
    try:
        entities_component = config.get_component('entities')
        entity_types = entities_component.get_entity_types()
        
        # Get the attributes for each entity type
        result = []
        for entity_type in entity_types:
            # Get the entity type definition
            type_info = entities_component.entity_types.get(entity_type, {})
            result.append({
                "name": entity_type,
                "attributes": type_info.get("attributes", {})
            })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Get a specific entity
@router.get("/api/entities/{entity_type}/{name}", response_class=JSONResponse)
async def get_entity(
    entity_type: str,
    name: str,
    config: Config = Depends(get_config)
):
    try:
        entities_component = config.get_component('entities')
        entity = entities_component.get_entity(entity_type, name)
        
        if not entity:
            raise HTTPException(status_code=404, detail=f"Entity {entity_type}:{name} not found")
        
        return {
            "name": entity.name,
            "entity_type": entity.entity_type,
            "attributes": entity.attributes,
            "dynamic_fields": {
                field: {
                    "original": info.get("original"),
                    "value": info.get("value")
                } for field, info in entity.dynamic_fields.items()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Create a new entity
@router.post("/api/entities", response_class=JSONResponse)
async def create_entity(
    name: str = Body(..., embed=True),
    entity_type: str = Body(..., embed=True),
    attributes: Dict[str, Any] = Body({}, embed=True),
    dynamic_fields: Dict[str, Dict[str, Any]] = Body({}, embed=True),
    config: Config = Depends(get_config)
):
    try:
        entities_component = config.get_component('entities')
        
        # Check if entity already exists
        if entities_component.get_entity(entity_type, name):
            raise HTTPException(status_code=400, detail=f"Entity {entity_type}:{name} already exists")
        
        # Process dynamic fields
        processed_dynamic_fields = {}
        for field_name, field_info in dynamic_fields.items():
            if "original" in field_info and field_info["original"]:
                expression = field_info["original"]
                
                # Evaluate the dynamic expression
                resolved_value, dynamic_info = dynamic_resolution_service.evaluate(
                    component_type="time_entity",
                    component_label=f"{entity_type}:{name}",
                    attribute=field_name,
                    expression=expression,
                )
                
                # Update the attributes with the resolved value
                attributes[field_name] = dynamic_info.latest_value
                
                # Store the dynamic field info
                processed_dynamic_fields[field_name] = {
                    "original": expression,
                    "value": dynamic_info.latest_value
                }
        
        # Create the entity
        entity = entities_component.create_entity(
            name=name,
            entity_type=entity_type,
            attributes=attributes,
            dynamic_fields=processed_dynamic_fields
        )
        
        return {
            "name": entity.name,
            "entity_type": entity.entity_type,
            "attributes": entity.attributes,
            "dynamic_fields": {
                field: {
                    "original": info.get("original"),
                    "value": info.get("value")
                } for field, info in entity.dynamic_fields.items()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Update an entity attribute
@router.put("/api/entities/{entity_type}/{name}/attributes/{attr_name}", response_class=JSONResponse)
async def update_entity_attribute(
    entity_type: str,
    name: str,
    attr_name: str,
    value: Any = Body(...),
    is_dynamic: bool = Body(False),
    original: Optional[str] = Body(None),
    config: Config = Depends(get_config)
):
    try:
        entities_component = config.get_component('entities')
        entity = entities_component.get_entity(entity_type, name)
        
        if not entity:
            raise HTTPException(status_code=404, detail=f"Entity {entity_type}:{name} not found")
        
        if is_dynamic and original:
            # Evaluate the dynamic expression
            resolved_value, dynamic_info = dynamic_resolution_service.evaluate(
                component_type="time_entity",
                component_label=f"{entity_type}:{name}",
                attribute=attr_name,
                expression=original,
            )
            
            # Set the dynamic attribute
            entities_component.set_dynamic_attribute(
                name=name,
                entity_type=entity_type,
                attr_name=attr_name,
                attr_value=dynamic_info.latest_value,
                original=original
            )
            
            return {
                "name": name,
                "entity_type": entity_type,
                "attribute": attr_name,
                "value": dynamic_info.latest_value,
                "is_dynamic": True,
                "original": original
            }
        else:
            # Update the attribute directly
            entities_component.update_entity_attribute(
                name=name,
                entity_type=entity_type,
                attr_name=attr_name,
                attr_value=value
            )
            
            return {
                "name": name,
                "entity_type": entity_type,
                "attribute": attr_name,
                "value": value,
                "is_dynamic": False,
                "original": None
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Delete an entity
@router.delete("/api/entities/{entity_type}/{name}", response_class=JSONResponse)
async def delete_entity(
    entity_type: str,
    name: str,
    config: Config = Depends(get_config)
):
    try:
        entities_component = config.get_component('entities')
        entity = entities_component.get_entity(entity_type, name)
        
        if not entity:
            raise HTTPException(status_code=404, detail=f"Entity {entity_type}:{name} not found")
        
        entities_component.remove_entity(name, entity_type)
        
        return {
            "status": "success",
            "message": f"Entity {entity_type}:{name} deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Rename an entity
@router.put("/api/entities/{entity_type}/{name}/rename", response_class=JSONResponse)
async def rename_entity(
    entity_type: str,
    name: str,
    new_name: str = Body(..., embed=True),
    config: Config = Depends(get_config)
):
    try:
        entities_component = config.get_component('entities')
        entity = entities_component.get_entity(entity_type, name)
        
        if not entity:
            raise HTTPException(status_code=404, detail=f"Entity {entity_type}:{name} not found")
        
        # Check if the new name already exists
        if entities_component.get_entity(entity_type, new_name):
            raise HTTPException(status_code=400, detail=f"Entity {entity_type}:{new_name} already exists")
        
        entities_component.rename_entity(name, new_name, entity_type)
        
        return {
            "status": "success",
            "message": f"Entity {entity_type}:{name} renamed to {entity_type}:{new_name} successfully",
            "old_name": name,
            "new_name": new_name,
            "entity_type": entity_type
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Evaluate an expression for an entity attribute
@router.post("/api/entities/{entity_type}/{name}/attributes/{attr_name}/evaluate", response_class=JSONResponse)
async def evaluate_entity_attribute_expression(
    entity_type: str,
    name: str,
    attr_name: str,
    expression: str = Body(...),
    config: Config = Depends(get_config)
):
    try:
        if not isinstance(expression, str) or not expression.startswith("("):
            return {
                "entity_type": entity_type,
                "name": name,
                "attribute": attr_name,
                "value": expression,
                "is_dynamic": False,
                "original": None
            }
        
        # Only evaluate without saving
        resolved_value, dynamic_info = dynamic_resolution_service.evaluate(
            component_type="time_entity",
            component_label=f"{entity_type}:{name}",
            attribute=attr_name,
            expression=expression
        )
        
        return {
            "entity_type": entity_type,
            "name": name,
            "attribute": attr_name,
            "value": resolved_value,
            "is_dynamic": True,
            "evaluated_value": str(resolved_value),
            "original": expression
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
