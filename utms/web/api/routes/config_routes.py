from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Union

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

from utms.core.config import UTMSConfig as Config
from utms.core.logger import get_logger
from utms.core.services.dynamic import dynamic_resolution_service
from utms.utms_types.field.types import FieldType, TypedValue, infer_type
from utms.web.api.models.config import ConfigFieldUpdatePayload
from utms.web.dependencies import get_config

router = APIRouter()
logger = get_logger()


@router.get("/api/config", response_class=JSONResponse)
async def get_config_data(config: Config = Depends(get_config)):
    config_data = {}
    all_items = config.config._config_manager.get_all()
    logger.debug(f"Fetching all config data. Found {len(all_items)} items.")

    for cfg_key, cfg_item in all_items.items():
        if not hasattr(cfg_item, "value") or not isinstance(cfg_item.value, TypedValue):
            logger.warning(
                f"Skipping config item '{cfg_key}' due to unexpected structure: {cfg_item}"
            )
            continue

        tv: TypedValue = cfg_item.value
        resolved_value = tv.value
        actual_field_type = tv.field_type
        is_dynamic = tv.is_dynamic
        original_code = tv.original
        reported_type_str = str(actual_field_type.value)
        api_value = resolved_value
        if isinstance(resolved_value, datetime):
            try:
                api_value = api_value.isoformat()
            except Exception as e:
                logger.warning(
                    f"Could not format datetime for key '{cfg_key}' to ISO string: {e}. Sending raw."
                )
                api_value = resolved_value
        elif isinstance(resolved_value, Decimal):
            api_value = str(resolved_value)
        item_data = {
            "key": cfg_key,
            "value": api_value,
            "type": reported_type_str,
            "is_dynamic": is_dynamic,
            "original": original_code,
            "enum_choices": getattr(tv, "enum_choices", None),
        }
        logger.debug(f"API data for '{cfg_key}': {item_data}")
        config_data[cfg_key] = item_data

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
    payload: ConfigFieldUpdatePayload,
    config: Config = Depends(get_config),
):
    try:
        actual_value_from_payload = payload.value
        value_type_str = payload.type
        is_dynamic = payload.is_dynamic or False
        original_expression = payload.original
        enum_choices = payload.enum_choices
        logger.debug("Received update payload for %s/%s: %s", key, field_name, payload.dict())
        config_item = config.config.get_config(key)
        if not config_item:
            raise ValueError(f"Config key {key} not found")

        typed_value: TypedValue

        if is_dynamic:
            expression_to_evaluate_and_store = original_expression
            logger.debug(
                f"Handling dynamic update for {key}/{field_name}. Expression: {expression_to_evaluate_and_store}"
            )
            if (
                not expression_to_evaluate_and_store
                or not isinstance(expression_to_evaluate_and_store, str)
                or not expression_to_evaluate_and_store.strip().startswith("(")
            ):
                logger.error(
                    f"Dynamic flag set for {key}/{field_name}, but 'original' payload field is missing, not a string, or not a Hy expression: {expression_to_evaluate_and_store}"
                )
                raise HTTPException(
                    status_code=400,
                    detail="Dynamic flag set, but 'original' field is missing or not a valid Hy expression starting with '('.",
                )
            try:
                resolved_value, dynamic_info = dynamic_resolution_service.evaluate(
                    component_type="config",
                    component_label=key,
                    attribute=field_name,
                    expression=expression_to_evaluate_and_store,
                )
                typed_value = TypedValue(
                    value=resolved_value,
                    field_type=FieldType.CODE,
                    is_dynamic=True,
                    original=expression_to_evaluate_and_store,
                )
                logger.debug(
                    f"Dynamic evaluation successful for {key}/{field_name}. Resolved: {resolved_value}, Type: {type(resolved_value)}"
                )
            except Exception as eval_error:
                logger.error(
                    f"Error evaluating dynamic expression for {key}/{field_name}: {eval_error}",
                    exc_info=True,
                )
                raise HTTPException(
                    status_code=400, detail=f"Error evaluating expression: {eval_error}"
                )
        else:
            logger.debug(
                f"Handling non-dynamic update for {key}/{field_name} with payload value: {actual_value_from_payload}, type_str: {value_type_str}"
            )

            field_type_enum: FieldType
            if value_type_str:
                try:
                    field_type_enum = FieldType.from_string(value_type_str)
                except ValueError:
                    logger.warning(
                        f"Invalid type string '{value_type_str}' received. Defaulting to STRING for {key}/{field_name}."
                    )
                    field_type_enum = FieldType.STRING
            else:
                logger.debug(
                    f"No type specified for {key}/{field_name}. Inferring type from value: {actual_value_from_payload}"
                )
                field_type_enum = infer_type(actual_value_from_payload)

            logger.debug(f"Determined FieldType for non-dynamic update: {field_type_enum}")

            try:
                typed_value = TypedValue(
                    value=actual_value_from_payload,  # The raw value from the payload
                    field_type=field_type_enum,  # The determined FieldType enum
                    is_dynamic=False,
                    original=None,
                    enum_choices=enum_choices if field_type_enum == FieldType.ENUM else None,
                    # item_type might be relevant if the payload contains list/dict items of a specific type
                )
                logger.info(
                    f"Successfully created TypedValue for non-dynamic update. Type: {typed_value.field_type}, Value: {typed_value.value}"
                )

            except Exception as e:  # Catch any error during TypedValue instantiation or conversion
                logger.error(
                    f"Error creating TypedValue for {key}/{field_name} with value '{actual_value_from_payload}' and type '{field_type_enum}': {e}",
                    exc_info=True,
                )
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid value '{actual_value_from_payload}' for specified type '{field_type_enum}'. Error: {e}",
                )

        if field_name == "value":
            config.config.update_config(key, typed_value)
            config.config.save()
        else:
            setattr(config_item, field_name, typed_value)
            config.config.save()
        updated_config_item = config.config.get_config(key)
        if not updated_config_item:
            raise HTTPException(
                status_code=500, detail="Failed to retrieve config item after update."
            )
        final_typed_value = updated_config_item.value
        return {
            "key": key,
            "field": field_name,
            "value": final_typed_value.value,
            "type": str(final_typed_value.field_type),
            "is_dynamic": final_typed_value.is_dynamic,
            "original": final_typed_value.original,
        }

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Unexpected error updating config {key}/{field_name}: {e}")
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")


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
                "original": None,
            }

        # Only evaluate without saving
        resolved_value, dynamic_info = dynamic_resolution_service.evaluate(
            component_type="config",
            component_label=key,
            attribute=field_name,
            expression=expression,
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
                original=value,
            )
        else:
            # Create TypedValue for non-dynamic value
            field_type = type if type else infer_type(value)
            typed_value = TypedValue(value=value, field_type=field_type)

        # Create the config with the typed value
        config.config.create_config(
            key=key,
            value=typed_value,
        )

        return {"status": "success", "message": f"Config {key} created successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
