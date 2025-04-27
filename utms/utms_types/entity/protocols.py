from typing import Any, Dict, Protocol, Optional, List

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

class TimeEntityManagerProtocol(Protocol):
    """Protocol for time entity manager"""
    
    def create(
        self,
        name: str,
        entity_type: str,
        attributes: Optional[Dict[str, Any]],
        dynamic_fields: Optional[Dict[str, Dict[str, Any]]],
    ) -> "TimeEntityProtocol": ...
    
    def get_by_name_and_type(self, name: str, entity_type: str) -> Optional["TimeEntityProtocol"]: ...
    
    def get_by_type(self, entity_type: str) -> List["TimeEntityProtocol"]: ...
    
    def get_by_attribute(self, attr_name: str, attr_value: Any) -> List["TimeEntityProtocol"]: ...
    
    def get_by_dynamic_field(self, field_name: str, is_dynamic: bool) -> List["TimeEntityProtocol"]: ...
    
    def serialize(self) -> Dict[str, Dict[str, Any]]: ...
    
    def deserialize(self, data: Dict[str, Dict[str, Any]]) -> None: ...
    
