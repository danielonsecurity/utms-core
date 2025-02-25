from typing import Any, Dict, Protocol

from .types import AttributeDefinition


class TimeEntityProtocol(Protocol):
    """Protocol for time entities"""

    attributes: Dict[str, AttributeDefinition]

    def __getattr__(self, name: str) -> Any: ...
    def __setattr__(self, name: str, value: Any) -> None: ...

    def get_attribute(self, name: str, default: Any = None) -> Any: ...
    def set_attribute(self, name: str, value: Any) -> None: ...


class TimeRange(Protocol):
    """Protocol for time range"""

    @property
    def start(self) -> "TimeStamp": ...

    @property
    def duration(self) -> "TimeLength": ...

    @property
    def end(self) -> "TimeStamp": ...

    def contains(self, timestamp: "TimeStamp") -> bool: ...
    def overlaps(self, other: "TimeRange") -> bool: ...
