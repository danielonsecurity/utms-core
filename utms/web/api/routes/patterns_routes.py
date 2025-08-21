# utms/web/api/routes/patterns_routes.py
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timedelta, time
from typing import List
import pytz

from utms.core.config import UTMSConfig
from utms.core.time import DecimalTimeStamp
from utms.core.hy.converter import converter

from utms.web.api.models.patterns import PatternPayload, OccurrenceEvent
from utms.web.dependencies import get_config

router = APIRouter()


@router.get("/api/patterns", response_model=List[PatternPayload], summary="Get all recurrence patterns")
async def get_all_patterns(utms_config: UTMSConfig = Depends(get_config)):
    """
    Retrieves all defined recurrence patterns and serializes them into a
    JSON-friendly format for the frontend.
    """
    pattern_component = utms_config.patterns
    patterns = pattern_component.get_all_patterns().values()
    response_payload = []

    for p in patterns:
        at_value = None
        if hasattr(p.spec, 'at_args') and p.spec.at_args:
            at_value = converter.model_to_py(p.spec.at_args, raw=True)
        elif hasattr(p.spec, 'times') and p.spec.times:
             at_value = p.spec.times

        on_value = None
        if hasattr(p.spec, 'weekdays') and p.spec.weekdays:
             weekday_map = {
                 0: "monday", 1: "tuesday", 2: "wednesday", 3: "thursday", 
                 4: "friday", 5: "saturday", 6: "sunday"
             }
             on_value = [weekday_map[day] for day in sorted(p.spec.weekdays)]

        payload = PatternPayload(
            label=p.label,
            name=p.name,
            every=p._original_interval or str(p.spec.interval),
            at=at_value,
            between=p.spec.start_time and p.spec.end_time and (p.spec.start_time, p.spec.end_time),
            on=on_value,
            except_between=p.spec.except_times and p.spec.except_times[0] if p.spec.except_times else None,
            groups=p.groups if hasattr(p, 'groups') else None
        )
        response_payload.append(payload)
    return response_payload


@router.post("/api/patterns", response_model=PatternPayload, status_code=201, summary="Create a new pattern")
async def create_pattern(payload: PatternPayload, utms_config: UTMSConfig = Depends(get_config)):
    """
    Creates a new recurrence pattern from the provided payload and saves it to disk.
    """
    pattern_component = utms_config.patterns
    if pattern_component.get_pattern(payload.label):
        raise HTTPException(status_code=409, detail=f"Pattern with label '{payload.label}' already exists.")
    
    try:
        # Create the pattern in memory
        pattern_component.create_pattern(
            label=payload.label, name=payload.name, every=payload.every,
            at=payload.at, between=payload.between, on=payload.on,
            except_between=payload.except_between, groups=payload.groups
        )
        # Persist all patterns to disk
        pattern_component.save()
        return payload
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/api/patterns/occurrences", response_model=List[OccurrenceEvent], summary="Get pattern occurrences for a date range")
async def get_pattern_occurrences(
    start: datetime, 
    end: datetime, 
    utms_config: UTMSConfig = Depends(get_config)
):
    """
    Calculates all occurrences of all patterns within a given time window.
    This endpoint is timezone-aware, using the 'default-timezone' from config.hy.
    """
    # --- TIMEZONE LOGIC ---
    try:
        config_component = utms_config.config
        tz_str = config_component.get_config("default-timezone").value.value
        local_tz = pytz.timezone(tz_str)
    except (AttributeError, pytz.UnknownTimeZoneError):
        # Fallback to UTC if config is missing or invalid to prevent crashes
        local_tz = pytz.utc
    
    # The incoming start/end times from FullCalendar already have timezone info.
    # We convert them to UTC to establish a consistent baseline for calculations.
    start_utc = start.astimezone(pytz.utc)
    end_utc = end.astimezone(pytz.utc)
    
    start_ts = DecimalTimeStamp(start_utc)
    end_ts = DecimalTimeStamp(end_utc)
    # --- END TIMEZONE LOGIC ---

    pattern_component = utms_config.patterns
    all_patterns = pattern_component.get_all_patterns().values()
    events = []
    
    for pattern in all_patterns:
        try:
            current_ts = pattern.next_occurrence(from_time=start_ts - 86400, local_tz=local_tz)
            
            # Safety loop to prevent infinite recursion on malformed patterns
            for _ in range(1000): 
                start_datetime = current_ts.to_gregorian()

                if start_datetime:
                    events.append(OccurrenceEvent(
                        title=pattern.name or pattern.label,
                        start=start_datetime.isoformat(),
                        extendedProps={"patternLabel": pattern.label}
                    ))
                
                # Find the next occurrence
                current_ts = pattern.next_occurrence(from_time=current_ts, local_tz=local_tz)
        except Exception as e:
            print(f"DEBUG: Caught exception for pattern '{pattern.label}'")
            breakpoint()
            print(f"Could not calculate occurrences for pattern '{pattern.label}': {e}")
    return events
