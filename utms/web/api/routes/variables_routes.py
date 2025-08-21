from typing import Any, Dict, Union

import hy
from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from hy.models import Expression, Symbol

from utms.core.config import UTMSConfig as Config
from utms.core.hy import evaluate_hy_expression
from utms.core.services.dynamic import dynamic_resolution_service
from utms.core.hy.converter import converter
from utms.utms_types.field.types import FieldType, TypedValue, infer_type
from utms.web.api.models.variables import (
    SerializedTypedValue,
    VariableResponse,
    VariableUpdatePayload,
)
from utms.web.dependencies import get_config

router = APIRouter()


@router.get(
    "/api/variables", response_model=Dict[str, VariableResponse], response_class=JSONResponse
)
async def get_variables(config: Config = Depends(get_config)):
    """
    Retrieves all variables, with their values serialized as TypedValue objects.
    For dynamic variables, their *resolved* value will be returned in the 'value' field.
    """
    variables_data = {}
    all_variable_models_view = config.variables.items()

    evaluation_context_for_api_display = {}
    for var_name_ctx, var_model_ctx in all_variable_models_view:
        if var_model_ctx.value.is_dynamic and isinstance(
            var_model_ctx.value.value, (Expression, Symbol)
        ):
            evaluation_context_for_api_display[var_name_ctx] = var_model_ctx.value.value
        else:
            evaluation_context_for_api_display[var_name_ctx] = var_model_ctx.value.value

        if "-" in var_name_ctx:
            underscore_key = var_name_ctx.replace("-", "_")
            if underscore_key not in evaluation_context_for_api_display:
                evaluation_context_for_api_display[underscore_key] = (
                    evaluation_context_for_api_display[var_name_ctx]
                )

    for var_name, variable_model in all_variable_models_view:
        typed_value_instance: TypedValue = variable_model.value

        display_value_for_api: Any
        if typed_value_instance.is_dynamic and isinstance(
            typed_value_instance.value, (Expression, Symbol)
        ):
            try:
                expr_to_eval_for_api = typed_value_instance.value

                config.logger.debug(
                    f"API Display: Re-evaluating dynamic var '{var_name}' using expr: {expr_to_eval_for_api}"
                )

                resolved_value_for_api, dynamic_info = dynamic_resolution_service.evaluate(
                    component_type="variable_api_display",
                    component_label=var_name,
                    attribute="value_display",
                    expression=expr_to_eval_for_api,
                    context=evaluation_context_for_api_display,
                )
                display_value_for_api = converter.model_to_py(resolved_value_for_api, raw=True)
            except Exception as e:
                display_value_for_api = f"ERROR: Could not resolve for API: {str(e)}"
                config.logger.error(
                    f"Error resolving dynamic variable '{var_name}' for API display: {e}",
                    exc_info=True,
                )
        else:
            display_value_for_api = typed_value_instance.value
            config.logger.debug(
                f"API Display: Using stored value for var '{var_name}': {display_value_for_api}"
            )

        original_from_model = typed_value_instance.original

        temp_serialized_typed_value = TypedValue(
            value=display_value_for_api,
            field_type=infer_type(display_value_for_api),
            is_dynamic=typed_value_instance.is_dynamic,
            original=original_from_model,
            item_type=typed_value_instance.item_type,
            enum_choices=typed_value_instance.enum_choices,
            item_schema_type=typed_value_instance.item_schema_type,
            referenced_entity_type=typed_value_instance.referenced_entity_type,
            referenced_entity_category=typed_value_instance.referenced_entity_category,
        )

        variables_data[var_name] = VariableResponse(
            key=variable_model.key,
            value=SerializedTypedValue(**temp_serialized_typed_value.serialize()),
        )
    return variables_data


@router.put("/api/variables/rename", response_class=JSONResponse)
async def rename_variable_key(
    old_key: str = Body(..., embed=True),
    new_key: str = Body(..., embed=True),
    config: Config = Depends(get_config),
):
    try:
        if old_key not in config.variables.get_variable(old_key):
            raise ValueError(f"Variable key {old_key} not found")

        config.variables.rename_variable_key(old_key, new_key)
        return {
            "old_key": old_key,
            "new_key": new_key,
            "status": "success",
            "message": f"Variable '{old_key}' renamed to '{new_key}'.",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/api/variables/{key}", response_model=VariableResponse, response_class=JSONResponse)
async def update_variable(
    key: str,
    payload: VariableUpdatePayload,  # Use the new payload model
    config: Config = Depends(get_config),
):
    """
    Updates the value of an existing variable.
    The new value can be static or a dynamic Hy expression.
    """
    try:
        # Extract values from payload
        value = payload.value
        is_dynamic = payload.is_dynamic
        original_expression = payload.original_expression
        field_type = payload.field_type

        # Call the component's update_variable method.
        # This method in VariableComponent will handle the TypedValue construction and internal logic.
        config.variables.update_variable(
            key=key,
            new_value=value,  # Pass raw value, component will handle Hy.read if dynamic
            is_dynamic=is_dynamic,
            original_expression=original_expression,
            field_type=field_type,
        )

        # Return the updated variable data
        variable_model = config.variables.get_variable(key)
        if not variable_model:
            raise HTTPException(
                status_code=500, detail="Variable not found after update (internal error)."
            )

        return VariableResponse(
            key=variable_model.key, value=SerializedTypedValue(**variable_model.value.serialize())
        )

    except ValueError as e:  # Catch ValueErrors for variable not found, etc.
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error updating variable: {str(e)}")


@router.post(
    "/api/variables/{key}/evaluate",
    response_model=SerializedTypedValue,
    response_class=JSONResponse,
)
async def evaluate_variable_expression(
    key: str,
    expression: str = Body(..., embed=True),  # Expression to evaluate
    config: Config = Depends(get_config),  # Add config to get variables context
):
    """
    Evaluates a given Hy expression using the current variable context without saving.
    Returns the resolved value as a serialized TypedValue.
    """
    try:
        # Get the context from the variable component (its items)
        # This context will be passed to the dynamic resolver.
        evaluation_context = {}
        variables_component_items = (
            config.variables.items()
        )  # This returns a dict of Variable models
        if variables_component_items:
            for var_name, var_model in variables_component_items.items():
                # For dynamic variables (HyExpressions), pass the HyExpression itself.
                # For static, pass the resolved Python value.
                if var_model.value.is_dynamic and isinstance(
                    var_model.value._raw_value, (Expression, Symbol)
                ):
                    evaluation_context[var_name] = var_model.value._raw_value
                else:
                    evaluation_context[var_name] = var_model.value.value

                # Also add underscore versions for Hy compatibility
                if "-" in var_name and var_name.replace("-", "_") not in evaluation_context:
                    evaluation_context[var_name.replace("-", "_")] = evaluation_context[var_name]

        # Convert string expression to HyExpression for evaluation
        hy_expression_to_evaluate = expression
        if (
            isinstance(expression, str)
            and expression.strip().startswith("(")
            and expression.strip().endswith(")")
        ):
            try:
                hy_expression_to_evaluate = hy.read(expression)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid Hy expression: {str(e)}")

        resolved_value, dynamic_info = dynamic_resolution_service.evaluate(
            component_type="variable_adhoc_eval",
            component_label=key,
            attribute="value",  # Placeholder, as this is ad-hoc evaluation
            expression=hy_expression_to_evaluate,
            context=evaluation_context,  # Pass the constructed context
        )

        # Create a temporary TypedValue to easily serialize the result for API consistency
        result_typed_value = TypedValue(
            value=resolved_value,
            field_type=infer_type(resolved_value),  # Infer actual type
            is_dynamic=dynamic_info.is_dynamic,
            original=dynamic_info.original,
        )

        return SerializedTypedValue(
            **result_typed_value.serialize()
        )  # Return the serialized TypedValue

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/api/variables/{key}", response_class=JSONResponse)
async def delete_variable(key: str, config: Config = Depends(get_config)):
    """
    Deletes a variable by its key.
    """
    try:
        if not config.variables.get_variable(key):  # Use get_variable for explicit check
            raise ValueError(f"Variable key '{key}' not found.")

        config.variables.remove_variable(key)
        return {"status": "success", "message": f"Variable '{key}' deleted successfully."}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error deleting variable: {str(e)}")


@router.post("/api/variables/{key}", response_model=VariableResponse, response_class=JSONResponse)
async def create_variable(
    key: str,  # Path parameter, no Body() here.
    payload: VariableUpdatePayload,  # Body parameter
    config: Config = Depends(get_config),
):
    """
    Creates a new variable with the given key (from path) and payload.
    """
    try:
        if config.variables.get_variable(key):
            raise ValueError(f"Variable '{key}' already exists.")

        value = payload.value
        is_dynamic = payload.is_dynamic
        original_expression = payload.original_expression
        field_type = payload.field_type

        variable_model = config.variables.create_variable(
            key=key,
            value=value,
            is_dynamic=is_dynamic,
            original_expression=original_expression,
            field_type=field_type,
        )

        return VariableResponse(
            key=variable_model.key, value=SerializedTypedValue(**variable_model.value.serialize())
        )

    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating variable: {str(e)}")
