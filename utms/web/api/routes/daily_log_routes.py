from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from utms.core.components.elements.daily_log import DailyLogComponent
from utms.core.config import UTMSConfig
from utms.core.logger import get_logger
from utms.web.api.models.log_entry import LogEntryResponse, SwitchContextRequest
from utms.web.dependencies import get_config

router = APIRouter()
logger = get_logger()


# Helper dependency to get the DailyLogComponent instance
def get_daily_log_component(config: UTMSConfig = Depends(get_config)) -> DailyLogComponent:
    component = config.get_component("daily_logs")
    if not isinstance(component, DailyLogComponent):
        raise HTTPException(status_code=500, detail="DailyLogComponent not available.")
    if not component.is_loaded:
        component.load()
    return component


@router.get(
    "/api/dailylog/{date_str}",
    # CHANGE this to use the new response model. Remove response_class.
    response_model=List[LogEntryResponse],
    summary="Get all context log entries for a specific day",
)
async def get_daily_log_api(
    date_str: str,  # Expects YYYY-MM-DD format
    daily_log_component: DailyLogComponent = Depends(get_daily_log_component),
):
    """
    Retrieves all logged context entries for a given date.
    """
    try:
        log_date = date.fromisoformat(date_str)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid date format. Please use YYYY-MM-DD.")

    try:
        log_entries = daily_log_component.get_log_for_day(log_date)

        # CHANGE the manual serialization to this clean, one-line conversion
        # using the factory method we defined on the Pydantic model.
        return [LogEntryResponse.from_core_log_entry(entry) for entry in log_entries]

    except Exception as e:
        logger.error(f"Error fetching daily log for {date_str}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal server error occurred.")


@router.post(
    "/api/dailylog/switch",
    response_model=List[LogEntryResponse],
    summary="Switch Current Context",
    description="Ends the currently active context and starts a new one, returning the updated list of contexts for today.",
)
async def switch_current_context(
    request: SwitchContextRequest,
    daily_log_component: DailyLogComponent = Depends(get_daily_log_component),
):
    """
    Switches the user's current context by name.
    """
    try:
        # The component method does all the heavy lifting
        updated_log_entries = daily_log_component.switch_context(request.context_name)

        # We return the full, updated list of entries for today,
        # formatted using our response model.
        return [LogEntryResponse.from_core_log_entry(entry) for entry in updated_log_entries]

    except Exception as e:
        logger.error(f"Failed to switch context to '{request.context_name}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while switching the context.",
        )
