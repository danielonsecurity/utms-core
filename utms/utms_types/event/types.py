from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class EventState(Enum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    CANCELLED = "CANCELLED"


class RepeatInterval(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    CUSTOM = "custom"


@dataclass
class Schedule:
    repeat: Optional[RepeatInterval] = None
    repeat_interval: Optional[int] = None  # e.g., every 2 weeks
    repeat_until: Optional[datetime] = None
    custom_repeat: Optional[str] = None  # for complex repeat rules


@dataclass
class TimeSpec:
    timestamp: datetime
    warning_period: Optional[str] = None  # e.g., "2d" for 2 days warning
    repeat: Optional[Schedule] = None


@dataclass
class Event:
    name: str
    state: EventState = EventState.TODO

    # Time specifications
    scheduled: Optional[TimeSpec] = None  # When the event is scheduled
    deadline: Optional[TimeSpec] = None  # When the event is due
    start_time: Optional[TimeSpec] = None  # When the event starts
    end_time: Optional[TimeSpec] = None  # When the event ends
    closed: Optional[datetime] = None  # When the event was marked as done

    # Orgmode-like properties
    priority: Optional[str] = None  # A, B, C
    tags: List[str] = None
    properties: Dict[str, Any] = None

    # UTMS specific
    anchor_refs: List[str] = None  # References to anchors
    uncertainty: Dict[str, float] = None  # Time uncertainty

    def __post_init__(self):
        self.tags = self.tags or []
        self.properties = self.properties or {}
        self.anchor_refs = self.anchor_refs or []
