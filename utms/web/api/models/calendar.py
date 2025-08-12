# utms/web/api/models/calendar.py (or entities.py)
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class CalendarEvent(BaseModel):
    id: str  # Unique ID for the event, e.g., "task:default:Lunch"
    title: str
    start: str  # ISO 8601 string
    end: Optional[str] = None
    allDay: bool = False
    color: Optional[str] = None # Allow custom colors
    extendedProps: Dict[str, Any] = Field(default_factory=dict)

class CalendarSource(BaseModel):
    entityType: str
    category: str
    attribute: str    
