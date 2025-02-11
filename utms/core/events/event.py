from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional


@dataclass
class EventConfig:
    """Configuration for an Event."""

    label: str
    name: Optional[str] = None
    state: str = ""
    schedule: Optional[Decimal] = None  # When event is scheduled
    deadline: Optional[Decimal] = None  # When event is due
    timestamp: Optional[Decimal] = None  # Point in time
    timerange: Optional[Dict[str, Decimal]] = None  # {'start': timestamp, 'end': timestamp}
    tags: List[str] = None
    properties: Dict[str, str] = None

    uid: Optional[str] = None
    all_day: bool = False
    location: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    created: Optional[Decimal] = None
    modified: Optional[Decimal] = None
    source: Optional[str] = None

    def __post_init__(self):
        self.name = self.name or self.label
        self.tags = self.tags or []
        self.properties = self.properties or {}


@dataclass
class Event:
    """Represents an event with various time specifications."""

    _config: EventConfig
    _created: datetime = None
    _closed: Optional[datetime] = None
    _clock_entries: List[tuple[Decimal, Optional[Decimal]]] = None

    def __post_init__(self):
        self._created = datetime.now()
        self._clock_entries = []

    @property
    def name(self) -> str:
        return self._config.name

    @property
    def state(self) -> str:
        return self._config.state

    @state.setter
    def state(self, value: str):
        self._config.state = value

    @property
    def schedule(self) -> Optional[Decimal]:
        return self._config.schedule

    @property
    def deadline(self) -> Optional[Decimal]:
        return self._config.deadline

    @property
    def timestamp(self) -> Optional[Decimal]:
        return self._config.timestamp

    @property
    def timerange(self) -> Optional[Dict[str, Decimal]]:
        return self._config.timerange

    @property
    def tags(self) -> List[str]:
        return self._config.tags

    @property
    def properties(self) -> Dict[str, str]:
        return self._config.properties

    @property
    def created(self) -> datetime:
        return self._created

    @property
    def closed(self) -> Optional[datetime]:
        return self._closed

    @closed.setter
    def closed(self, value: datetime):
        self._closed = value
