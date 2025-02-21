from typing import Dict, List
from .time_specs import TimeStampSpec, TimeRangeSpec, ClockEntry, CompletionRecord, TimeTracking
from .types import AttributeDefinition

# Core attributes that most entities will use
CORE_ATTRIBUTES = {
    # Time-related
    'scheduled': AttributeDefinition(TimeStampSpec),     
    'deadline': AttributeDefinition(TimeStampSpec),
    'timestamps': AttributeDefinition(List[TimeStampSpec], default_factory=list),  

    # Metadata
    'state': AttributeDefinition(str, default=""),
    'tags': AttributeDefinition(List[str], default_factory=list),
    'priority': AttributeDefinition(str),
}

# Additional attributes
EXTENDED_ATTRIBUTES = {
    'ranges': AttributeDefinition(List[TimeRangeSpec]),
    'clock_entries': AttributeDefinition(List[ClockEntry]),  
    'completion_history': AttributeDefinition(List[CompletionRecord]),
    'time_tracking': AttributeDefinition(List[TimeTracking]),
    'description': AttributeDefinition(str),
    'location': AttributeDefinition(str),
    'urls': AttributeDefinition(List[str]),
}
