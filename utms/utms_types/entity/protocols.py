from typing import Any, Dict, List, Optional, Protocol

from .types import AttributeDefinition


class EntityProtocol(Protocol):
    """Protocol for entities"""

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


class EntityManagerProtocol(Protocol):
    """Protocol for time entity manager"""

    def create(
        self,
        name: str,
        entity_type: str,
        attributes: Optional[Dict[str, Any]],
        dynamic_fields: Optional[Dict[str, Dict[str, Any]]],
    ) -> "EntityProtocol": ...

    def get_by_name_and_type(self, name: str, entity_type: str) -> Optional["EntityProtocol"]: ...

    def get_by_type(self, entity_type: str) -> List["EntityProtocol"]: ...

    def get_by_attribute(self, attr_name: str, attr_value: Any) -> List["EntityProtocol"]: ...

    def get_by_dynamic_field(self, field_name: str, is_dynamic: bool) -> List["EntityProtocol"]: ...

    def serialize(self) -> Dict[str, Dict[str, Any]]: ...

    def deserialize(self, data: Dict[str, Dict[str, Any]]) -> None: ...
