from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from utms.core.models.elements.log_entry import LogEntry as CoreLogEntry


# Model for the POST /switch request body
class SwitchContextRequest(BaseModel):
    """Request body for switching the current context."""

    context_name: str = Field(..., description="The name of the new context to switch to.")


# Model for the API response for a single log entry
class LogEntryResponse(BaseModel):
    """
    Represents a single flattened log entry for API responses,
    making it easy for frontends to consume.
    """

    context_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    color: Optional[str] = None

    class Config:
        from_attributes = True

    @classmethod
    def from_core_log_entry(cls, core_entry: CoreLogEntry) -> "LogEntryResponse":
        """
        A factory method to create an API response model from our internal
        core LogEntry object. It flattens the 'attributes' dict.
        """
        # Safely get TypedValue objects from the attributes dict
        start_time_tv = core_entry.attributes.get("start_time")
        end_time_tv = core_entry.attributes.get("end_time")
        color_tv = core_entry.attributes.get("color")

        # Extract the actual .value from the TypedValue, or None if it doesn't exist
        return cls(
            context_name=core_entry.context_name,
            start_time=start_time_tv.value if start_time_tv else None,
            end_time=end_time_tv.value if end_time_tv else None,
            color=color_tv.value if color_tv else None,
        )
