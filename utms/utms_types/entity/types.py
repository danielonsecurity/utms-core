from typing import Any, Callable, Dict, List, Optional, Protocol, Type, Union

from ..base.protocols import TimeRange, TimeStamp
from .properties import EntityPropertiesProtocol, PropertyDefinition
from .time_specs import ClockEntry, CompletionRecord, TimeRangeSpec, TimeStampSpec, TimeTracking


class AttributeProtocol(Protocol):
    """Protocol for attribute definitions"""

    name: str
    type: Type
    required: bool
    default: Any


class TimeEntityProtocol(Protocol):
    """Protocol for time entities"""

    properties_class: Type[EntityPropertiesProtocol]
    attributes: Dict[str, AttributeProtocol]
    properties: EntityPropertiesProtocol


# Types for attribute values
AttributeValue = Union[
    TimeStamp,
    TimeRange,
    TimeStampSpec,
    TimeRangeSpec,
    List[TimeStampSpec],
    List[TimeRangeSpec],
    List[ClockEntry],
    List[CompletionRecord],
    str,
    List[str],
    Dict[str, Any],
    bool,
    None,
]


class AttributeDefinition:
    """Defines a time-related attribute"""

    def __init__(
        self,
        type_: Type[AttributeValue],
        required: bool = False,
        default: AttributeValue = None,
        default_factory: Optional[Callable[[], AttributeValue]] = None,
    ):
        self.type = type_
        self.required = required
        self.default = default
        self.default_factory = default_factory

        if default is not None and default_factory is not None:
            raise ValueError("Cannot specify both default and default_factory")
