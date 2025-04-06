from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from typing import Union, Any

from utms.core.config import Config
from utms.web.api import templates
from utms.web.dependencies import get_config
from utms.core.hy import evaluate_hy_expression

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
        breakpoint()
        # Update the config value
        config.config[key] = value
        config.config.save()

        # Check if the value is a dynamic Hy expression
        if isinstance(value, str) and value.startswith('('):
            try:
                # Evaluate the Hy expression
                evaluated_value = evaluate_hy_expression(value)
                breakpoint()
                return {
                    "value": value,
                    "is_dynamic": True,
                    "evaluated_value": str(evaluated_value)
                }
            except Exception as eval_error:
                return {
                    "value": value,
                    "is_dynamic": True,
                    "evaluated_value": f"Evaluation Error: {str(eval_error)}"
                }

        # For non-dynamic values, return standard response
        return {
            "value": value,
            "is_dynamic": False
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
        # Check if the old key exists
        if old_key not in config.config:
            raise ValueError(f"Config key {old_key} not found")

        # Get the value of the old key
        value = config.config[old_key]

        # Remove the old key and add the new key with the same value
        del config.config[old_key]
        config.config[new_key] = value

        # Save the updated configuration
        config.config.save()

        return {
            "old_key": old_key,
            "new_key": new_key,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
