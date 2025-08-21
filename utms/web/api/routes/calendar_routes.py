# utms/web/api/routes/calendar_routes.py
from fastapi import APIRouter, Depends, Query
from datetime import datetime, time
from typing import List, Dict, Any, Set
import pytz

from utms.core.config import UTMSConfig
from utms.core.time import DecimalTimeStamp
from utms.utms_types.field.types import FieldType
from utms.web.dependencies import get_config
from utms.web.api.models.calendar import CalendarEvent, CalendarSourceRequest
from pydantic import BaseModel

router = APIRouter()

COLOR_MAP = {
    "recurrence": "#1976d2",  
    "deadline": "#d32f2f",    
    "default": "#757575"      
}

@router.post("/api/calendar/events", response_model=List[CalendarEvent], summary="Get planned and actual events for the calendar")
async def get_calendar_events(
    start: datetime,
    end: datetime,
    sources: List[CalendarSourceRequest],
    include: Set[str] = Query(default={"planned", "actual"}),
    utms_config: UTMSConfig = Depends(get_config)
):
    events: List[CalendarEvent] = []
    entities_component = utms_config.entities
    pattern_component = utms_config.patterns

    # --- Timezone logic (no changes) ---
    try:
        tz_str = utms_config.config.get_config("default-timezone").value.value
        local_tz = pytz.timezone(tz_str)
    except Exception:
        local_tz = pytz.utc

    start_utc = start.astimezone(pytz.utc)
    end_utc = end.astimezone(pytz.utc)
    start_ts = DecimalTimeStamp(start_utc)
    end_ts = DecimalTimeStamp(end_utc)

    all_relevant_entities = []
    for source in sources:
        categories_to_fetch = entities_component.get_categories(source.entityType) if source.category == '*' else [source.category]
        for category in categories_to_fetch:
            all_relevant_entities.extend(entities_component.get_by_type(source.entityType, category))
    
    processed_entity_ids = set()

    for entity in all_relevant_entities:
        entity_id = entity.get_identifier()
        if entity_id in processed_entity_ids:
            continue
        processed_entity_ids.add(entity_id)

        if "actual" in include and entity.has_attribute("occurrences"):
            # The EntityLoader already resolved this into a clean Python list of dicts.
            # We can use it directly without any conversion.
            occurrences_list = entity.get_attribute_value("occurrences")
            if not isinstance(occurrences_list, list):
                continue

            for occ_dict in occurrences_list:
                try:
                    # The values are already datetime objects.
                    occ_start = occ_dict.get('start_time')
                    occ_end = occ_dict.get('end_time')

                    if not isinstance(occ_start, datetime) or not isinstance(occ_end, datetime):
                        continue

                    occ_start_utc = occ_start if occ_start.tzinfo else occ_start.replace(tzinfo=pytz.utc)
                    occ_end_utc = occ_end if occ_end.tzinfo else occ_end.replace(tzinfo=pytz.utc)

                    if occ_start_utc < end_utc and occ_end_utc > start_utc:
                        events.append(CalendarEvent(
                            id=f"{entity_id}:occ:{occ_start_utc.isoformat()}",
                            title=entity.name,
                            start=occ_start_utc.isoformat(),
                            end=occ_end_utc.isoformat(),
                            backgroundColor="#4caf50", # Solid green
                            borderColor="#388e3c",     # Darker green border
                            textColor="white",
                            extendedProps={"entityId": entity_id, "type": "actual"}
                        ))
                except Exception:
                    continue
        if "planned" in include and entity.has_attribute("recurrence"):
            typed_value = entity.get_attribute_typed("recurrence")
            if not (typed_value and typed_value.value):
                continue

            pattern_label = str(typed_value.value).split(":")[-1]
            pattern = pattern_component.get_pattern(pattern_label)
            if not pattern:
                continue

            try:
                # Start searching from the beginning of the calendar view
                current_ts = pattern.next_occurrence(from_time=start_ts - 86400, local_tz=local_tz)
                
                # Safety loop
                while current_ts < end_ts:
                    start_dt = current_ts.to_gregorian()
                    
                    # For patterns with a 'between' clause, we can calculate an end time
                    end_dt = None
                    if pattern.spec.start_time and pattern.spec.end_time:
                        duration_start = datetime.strptime(pattern.spec.start_time, "%H:%M")
                        duration_end = datetime.strptime(pattern.spec.end_time, "%H:%M")
                        duration = duration_end - duration_start
                        end_dt = start_dt + duration
                    
                    events.append(CalendarEvent(
                        id=f"{entity_id}:planned:{start_dt.isoformat()}",
                        title=f"{entity.name} (Planned)",
                        start=start_dt.isoformat(),
                        end=end_dt.isoformat() if end_dt else None,
                        backgroundColor="rgba(25, 118, 210, 0.2)", # Transparent blue
                        borderColor="#1976d2",                      # Solid blue border
                        textColor="#1565c0",
                        extendedProps={"entityId": entity_id, "type": "planned"}
                    ))
                    
                    current_ts = pattern.next_occurrence(from_time=current_ts, local_tz=local_tz)

            except (RuntimeError, ValueError) as e:
                print(f"Could not calculate planned occurrences for {entity.name}: {e}")
                continue                
    return events
