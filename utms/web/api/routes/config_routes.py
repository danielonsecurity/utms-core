from typing import Any, Union, Dict
from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

from utms.core.config import Config
from utms.core.models.config import Config as ConfigModel
from utms.core.hy import evaluate_hy_expression
from utms.core.services.dynamic import dynamic_resolution_service
from utms.web.api import templates
from utms.web.dependencies import get_config

router = APIRouter()

@router.get("/api/config", response_class=JSONResponse)
async def get_config_data(config: Config = Depends(get_config)):
    return config.config

@router.put("/api/config/{key}", response_class=JSONResponse)
async def update_config(
    key: str, 
    value: Union[str, int, float, list] = Body(...), 
    config: Config = Depends(get_config)
):
    try:
        # Check if the value is a dynamic Hy expression
        if isinstance(value, str) and value.startswith("("):
            try:
                breakpoint()
                # Register and evaluate the dynamic expression
                resolved_value, dynamic_info = dynamic_resolution_service.evaluate(
                    component_type="config",
                    component_label=key,
                    attribute="value",
                    expression=value
                )
                
                # Update config with the evaluated value and expression
                config.config[key] = ConfigModel(key=key,
                                                 value=dynamic_info.latest_value,
                                                 is_dynamic=True,
                                                 original=value)  # Store the original expression
                config.config.save()
                
                return dynamic_info.to_dict()
            except Exception as eval_error:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Error evaluating expression: {str(eval_error)}"
                )
        else:
            # For non-dynamic values
            config.config[key] = value
            config.config.save()
            return {
                "value": value,
                "is_dynamic": False,
                "original": None
            }
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/api/config/{key}/evaluate", response_class=JSONResponse)
async def evaluate_config_expression(
    key: str,
    expression: str = Body(...),
):
    try:
        if not isinstance(expression, str) or not expression.startswith("("):
            return {
                "value": expression,
                "is_dynamic": False,
                "original": None
            }
            
        # Only evaluate without saving
        resolved_value, dynamic_info = dynamic_resolution_service.evaluate(
            component_type="config",
            component_label=key,
            attribute="value",
            expression=expression
        )
        
        return {
            "value": resolved_value,
            "is_dynamic": True,
            "evaluated_value": str(resolved_value),
            "original": expression
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/api/config/rename", response_class=JSONResponse)
async def rename_config_key(
    old_key: str = Body(...),
    new_key: str = Body(...),
    config: Config = Depends(get_config)
):
    try:
        if old_key not in config.config:
            raise ValueError(f"Config key {old_key} not found")

        value = config.config[old_key]
        del config.config[old_key]
        config.config[new_key] = value
        config.config.save()

        return {"old_key": old_key, "new_key": new_key, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
