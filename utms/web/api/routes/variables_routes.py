from typing import Any, Dict, Union

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

from utms.core.config import UTMSConfig as Config
from utms.core.hy import evaluate_hy_expression
from utms.core.services.dynamic import dynamic_resolution_service
from utms.web.dependencies import get_config

router = APIRouter()


@router.get("/api/variables", response_class=JSONResponse)
async def get_variables(config: Config = Depends(get_config)):
    variables_data = {}
    for var_name, var_prop in config.variables.items():
        # Create a base variable object with all fields
        variable_data = {
            "key": var_name,
            "value": var_prop.value,
            "dynamic_fields": var_prop.dynamic_fields
        }
        variables_data[var_name] = variable_data
    return variables_data


@router.put("/api/variables/rename", response_class=JSONResponse)
async def rename_variable_key(
    old_key: str = Body(..., embed=True),
    new_key: str = Body(..., embed=True),
    config: Config = Depends(get_config),
):
    try:
        if old_key not in config.variables:
            raise ValueError(f"Variable key {old_key} not found")

        config.variables.rename_variable_key(old_key, new_key)
        return {"old_key": old_key, "new_key": new_key, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/api/variables/{key}/fields/{field_name}", response_class=JSONResponse)
async def update_variable_field(
    key: str, 
    field_name: str,
    value: Union[str, int, float, list, dict] = Body(...), 
    config: Config = Depends(get_config)
):
    try:
        variable = config.variables.get_variable(key)
        if not variable:
            raise ValueError(f"Variable key {key} not found")
            
        # Check if the value is a dynamic Hy expression
        if isinstance(value, str) and value.startswith("("):
            try:
                # Register and evaluate the dynamic expression
                resolved_value, dynamic_info = dynamic_resolution_service.evaluate(
                    component_type="variable",
                    component_label=key,
                    attribute=field_name,
                    expression=value,
                )

                # Update variable with the evaluated value and expression
                config.variables.set_dynamic_field(
                    key=key,
                    field_name=field_name,
                    value=dynamic_info.latest_value,
                    original=value
                )

                return {
                    "key": key,
                    "field": field_name,
                    "value": dynamic_info.latest_value,
                    "is_dynamic": True,
                    "original": value,
                }
            except Exception as eval_error:
                raise HTTPException(
                    status_code=400, detail=f"Error evaluating expression: {str(eval_error)}"
                )
        else:
            # For non-dynamic values, update the field directly
            if field_name == "value":
                config.variables.update_variable(key, value)
            else:
                # For other fields, we need to set the attribute and save
                setattr(variable, field_name, value)
                
                # Remove any dynamic field info if it exists
                if field_name in variable.dynamic_fields:
                    dynamic_fields = variable.dynamic_fields.copy()
                    dynamic_fields.pop(field_name, None)
                    
                    # Create a new variable with updated dynamic fields
                    config.variables._variable_manager.create(
                        key=key,
                        value=variable.value,
                        dynamic_fields=dynamic_fields
                    )
                
                config.variables.save()
            
            # Return the updated variable data
            variable = config.variables.get_variable(key)
            return {
                "key": key,
                "field": field_name,
                "value": getattr(variable, field_name),
                "is_dynamic": variable.is_field_dynamic(field_name),
                "original": variable.get_original_expression(field_name)
            }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/variables/{key}/fields/{field_name}/evaluate", response_class=JSONResponse)
async def evaluate_variable_field_expression(
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
            component_type="variable", 
            component_label=key, 
            attribute=field_name, 
            expression=expression
        )

        return {
            "key": key,
            "field": field_name,
            "value": resolved_value,
            "is_dynamic": True,
            "evaluated_value": str(resolved_value),
            "original": expression,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/api/variables/{key}", response_class=JSONResponse)
async def delete_variable(key: str, config: Config = Depends(get_config)):
    try:
        if key not in config.variables:
            raise ValueError(f"Variable key {key} not found")

        config.variables.remove_variable(key)
        return {"status": "success", "message": f"Variable {key} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/variables", response_class=JSONResponse)
async def create_variable(
    key: str = Body(..., embed=True),
    value: Any = Body(..., embed=True),
    is_dynamic: bool = Body(False, embed=True),
    config: Config = Depends(get_config),
):
    try:
        if key in config.variables:
            raise ValueError(f"Variable {key} already exists")

        dynamic_fields = {}
        
        if is_dynamic and isinstance(value, str) and value.startswith("("):
            # Evaluate the dynamic expression
            resolved_value, dynamic_info = dynamic_resolution_service.evaluate(
                component_type="variable",
                component_label=key,
                attribute="value",
                expression=value,
            )

            # Set up dynamic field for value
            dynamic_fields["value"] = {
                "original": value,
                "value": dynamic_info.latest_value
            }
            
            # Use the evaluated value
            actual_value = dynamic_info.latest_value
        else:
            # Use the provided value directly
            actual_value = value
            
        # Create the variable with the appropriate fields
        config.variables.create_variable(
            key=key,
            value=actual_value,
            dynamic_fields=dynamic_fields
        )

        return {"status": "success", "message": f"Variable {key} created successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
