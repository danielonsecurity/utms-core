# utms/web/api/models/patterns.py
from typing import List, Optional, Union, Tuple
from pydantic import BaseModel, Field

class AtClause(BaseModel):
    type: str  # "time" or "minute"
    value: Union[str, int, List[str]]

class PatternPayload(BaseModel):
    label: str = Field(..., description="The unique identifier for the pattern (e.g., 'HOURLY-AT-25').")
    name: Optional[str] = Field(None, description="A user-friendly display name.")
    every: str = Field(..., description="The recurrence interval, e.g., '1h', '2 days', '15m'.")
    at: Optional[List[Union[str, List[Union[str, int]]]]] = Field(None, description="Specifies times, e.g., ['10:00', '14:00'] or [[':minute', 25]].")
    between: Optional[Tuple[str, str]] = Field(None, description="A time window, e.g., ['09:00', '17:00'].")
    on: Optional[List[str]] = Field(None, description="Days of the week, e.g., ['monday', 'friday'].")
    except_between: Optional[Tuple[str, str]] = Field(None, description="An exclusion window.")
    groups: Optional[List[str]] = Field(None)

class OccurrenceEvent(BaseModel):
    title: str
    start: str  # ISO 8601 string
    allDay: bool = False
    extendedProps: dict = Field(default_factory=dict)
