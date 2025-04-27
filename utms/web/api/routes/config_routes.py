from typing import Any, Dict, Union

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

from utms.core.config import UTMSConfig as Config
from utms.core.hy import evaluate_hy_expression
from utms.core.services.dynamic import dynamic_resolution_service
from utms.web.dependencies import get_config
from utms.utms_types.field.types import TypedValue, FieldType, infer_type

router = APIRouter()


@router.get("/api/config", response_class=JSONResponse)
async def get_config_data(config: Config = Depends(get_config)):
    config_data = {}
    for config_key, config_item in config.config.items():
        # Create a serializable representation of the config
        typed_value = config_item.value
        
        config_data[config_key] = {
            "key": config_key,
            "value": typed_value.value,  # The actual value
            "type": str(typed_value.field_type),  # Type information
            "is_dynamic": typed_value.is_dynamic,
            "original": typed_value.original if typed_value.is_dynamic else None,
            "enum_choices": typed_value.enum_choices if hasattr(typed_value, 'enum_choices') else None
        }
    return config_data

@router.put("/api/config/rename", response_class=JSONResponse)
async def rename_config_key(
    old_key: str = Body(..., embed=True),
    new_key: str = Body(..., embed=True),
    config: Config = Depends(get_config),
):
    try:
        config.config.rename_config_key(old_key, new_key)
        return {"old_key": old_key, "new_key": new_key, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/api/config/{key}/fields/{field_name}", response_class=JSONResponse)
async def update_config_field(
    key: str, 
    field_name: str,
    value: Union[str, int, float, list, dict] = Body(...), 
    config: Config = Depends(get_config)
):
    try:
        config_item = config.config.get_config(key)
        if not config_item:
            raise ValueError(f"Config key {key} not found")
            
        # Check if the value is a dynamic Hy expression
        if isinstance(value, str) and value.startswith("("):
            try:
                # Register and evaluate the dynamic expression
                resolved_value, dynamic_info = dynamic_resolution_service.evaluate(
                    component_type="config",
                    component_label=key,
                    attribute=field_name,
                    expression=value,
                )

                # Infer type from resolved value or use string as default
                field_type = FieldType.CODE  # Use CODE for expressions
                
                typed_value = TypedValue(
                    value=dynamic_info.latest_value,
                    field_type=field_type,
                    is_dynamic=True,
                    original=value
                )
                
                # Update config with the typed value
                if field_name == "value":
                    config.config.update_config(key, typed_value)
                else:
                    # For other fields, set the attribute
                    setattr(config_item, field_name, typed_value)
                    config.config.save()

                return {
                    "key": key,
                    "field": field_name,
                    "value": dynamic_info.latest_value,
                    "type": str(field_type),
                    "is_dynamic": True,
                    "original": value,
                }
            except Exception as eval_error:
                raise HTTPException(
                    status_code=400, detail=f"Error evaluating expression: {str(eval_error)}"
                )
        else:
            
            # Infer the field type from the value
            field_type = infer_type(value)
            typed_value = TypedValue(value=value, field_type=field_type)
            
            if field_name == "value":
                config.config.update_config(key, typed_value)
            else:
                # For other fields, set the attribute
                setattr(config_item, field_name, typed_value)
                config.config.save()
            
            # Return the updated config data
            config_item = config.config.get_config(key)
            
            return {
                "key": key,
                "field": field_name,
                "value": typed_value.value,
                "type": str(field_type),
                "is_dynamic": False,
                "original": None
            }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/config/{key}/fields/{field_name}/evaluate", response_class=JSONResponse)
async def evaluate_config_field_expression(
    key: str,
    field_name: str,
    expression: str = Body(...),
):
    try:
        if not isinstance(expression, str) or not expression.startswith("("):
            return {
                "key": key,
                "field": field_name,
                "value": expression, 
                "is_dynamic": False, 
                "original": None
            }

        # Only evaluate without saving
        resolved_value, dynamic_info = dynamic_resolution_service.evaluate(
            component_type="config", 
            component_label=key, 
            attribute=field_name, 
            expression=expression
        )

        # Infer the type from the resolved value
        value_type = infer_type(resolved_value)

        return {
            "key": key,
            "field": field_name,
            "value": resolved_value,
            "type": str(value_type),
            "is_dynamic": True,
            "evaluated_value": str(resolved_value),
            "original": expression,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/api/config/{key}", response_class=JSONResponse)
async def delete_config(key: str, config: Config = Depends(get_config)):
    try:
        config.config.remove_config(key)
        return {"status": "success", "message": f"Config {key} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/config", response_class=JSONResponse)
async def create_config(
    key: str = Body(..., embed=True),
    value: Any = Body(..., embed=True),
    type: str = Body(None, embed=True),  # Optional type information
    is_dynamic: bool = Body(False, embed=True),
    config: Config = Depends(get_config),
):
    try:
        if key in config.config:
            raise ValueError(f"Config {key} already exists")

        
        
        if is_dynamic and isinstance(value, str) and value.startswith("("):
            # Evaluate the dynamic expression
            resolved_value, dynamic_info = dynamic_resolution_service.evaluate(
                component_type="config",
                component_label=key,
                attribute="value",
                expression=value,
            )

            # Create TypedValue with dynamic properties
            field_type = type if type else FieldType.CODE
            typed_value = TypedValue(
                value=dynamic_info.latest_value,
                field_type=field_type,
                is_dynamic=True,
                original=value
            )
        else:
            # Create TypedValue for non-dynamic value
            field_type = type if type else infer_type(value)
            typed_value = TypedValue(
                value=value,
                field_type=field_type
            )
            
        # Create the config with the typed value
        config.config.create_config(
            key=key,
            value=typed_value,
        )

        return {"status": "success", "message": f"Config {key} created successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
