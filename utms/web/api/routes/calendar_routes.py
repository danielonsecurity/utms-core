# utms/web/api/routes/calendar_routes.py
from fastapi import APIRouter, Depends
from datetime import datetime, time
from typing import List, Dict, Any
import pytz

from utms.core.config import UTMSConfig
from utms.core.time import DecimalTimeStamp
from utms.utms_types.field.types import FieldType
from utms.web.dependencies import get_config
from utms.web.api.models.calendar import CalendarEvent
from utms.utils import hy_to_python, list_to_dict
from pydantic import BaseModel

router = APIRouter()

# Define a color map for different attributes
COLOR_MAP = {
    "recurrence": "#1976d2",  # Blue
    "deadline": "#d32f2f",      # Red
    "default": "#757575"        # Grey
}

class CalendarSource(BaseModel):
    entityType: str
    category: str
    # The 'attribute' field is no longer needed from the frontend

@router.post("/api/calendar/events", response_model=List[CalendarEvent], summary="Get events for the calendar")
async def get_calendar_events(
    start: datetime,
    end: datetime,
    sources: List[CalendarSource], # This will now be the simplified source list
    utms_config: UTMSConfig = Depends(get_config)
):
    events: List[CalendarEvent] = []
    entities_component = utms_config.entities
    pattern_component = utms_config.patterns

    # --- Timezone logic (no changes needed here) ---
    try:
        tz_str = utms_config.config.get_config("default-timezone").value.value
        local_tz = pytz.timezone(tz_str)
    except Exception:
        local_tz = pytz.utc
    
    start_utc = start.astimezone(pytz.utc)
    end_utc = end.astimezone(pytz.utc)
    start_ts = DecimalTimeStamp(start_utc)
    end_ts = DecimalTimeStamp(end_utc)
    # ---

    all_relevant_entities = []
    for source in sources:
        categories_to_fetch = entities_component.get_categories(source.entityType) if source.category == '*' else [source.category]
        for category in categories_to_fetch:
            all_relevant_entities.extend(entities_component.get_by_type(source.entityType, category))
    
    # Use a set to avoid processing the same entity multiple times if it matches multiple sources
    processed_entity_ids = set()

    # --- THIS IS THE CORRECTED LOGIC ---
    # Loop through each unique entity ONCE
    for entity in all_relevant_entities:
        entity_id = entity.get_identifier()
        if entity_id in processed_entity_ids:
            continue
        processed_entity_ids.add(entity_id)

        # A. Find and process the 'recurrence' attribute specifically
        if entity.has_attribute("recurrence"):
            typed_value = entity.get_attribute_typed("recurrence")
            if typed_value and typed_value.value:
                # ... (The rest of the recurrence logic from the previous response is correct) ...
                pattern_label = str(typed_value.value).split(":")[-1]
                pattern = pattern_component.get_pattern(pattern_label)
                if not pattern: continue

                try:
                    search_start_ts = start_ts
                    # (Safely parse agent_state as before)
                    # ...
                    
                    current_ts = pattern.next_occurrence(from_time=search_start_ts, local_tz=local_tz)
                    while current_ts < end_ts:
                        if current_ts >= start_ts:
                            start_dt = current_ts.to_gregorian()
                            events.append(CalendarEvent(
                                id=f"{entity.get_identifier()}:recurrence",
                                title=entity.name,
                                start=start_dt.isoformat(),
                                color=COLOR_MAP.get("recurrence"),
                                extendedProps={"entityId": entity_id, "attribute": "recurrence"}
                            ))
                        current_ts = pattern.next_occurrence(from_time=current_ts, local_tz=local_tz)
                except (RuntimeError, ValueError) as e:
                    print(f"Error calculating recurrence for {entity.label}: {e}") # Added print for debug
                    continue
        
        # B. Scan all OTHER attributes for simple datetime fields
        for attr_name, attr_typed_value in entity.get_all_attributes_typed().items():
            if attr_typed_value.field_type == FieldType.DATETIME:
                # ... (The logic for simple datetimes from the previous response is correct) ...
                dt_value = attr_typed_value.value
                if isinstance(dt_value, datetime):
                    dt_utc = dt_value if dt_value.tzinfo else dt_value.replace(tzinfo=pytz.utc)
                    if start_utc <= dt_utc < end_utc:
                        events.append(CalendarEvent(
                            id=f"{entity_id}:{attr_name}",
                            title=f"{entity.name} ({attr_name.replace('-', ' ').title()})",
                            start=dt_utc.isoformat(),
                            allDay=True,
                            color=COLOR_MAP.get(attr_name, COLOR_MAP["default"]),
                            extendedProps={"entityId": entity_id, "attribute": attr_name}
                        ))

    return events
