from dataclasses import dataclass
from enum import Enum
from typing import Callable, List, Optional, Protocol, Set, Union

from utms.core.time import DecimalTimeLength, DecimalTimeStamp

# Type aliases
ModifierFunc = Callable[[DecimalTimeStamp], DecimalTimeStamp]
ConstraintFunc = Callable[[DecimalTimeStamp], bool]


class FrequencyType(str, Enum):
    SECONDLY = "secondly"
    MINUTELY = "minutely"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    CUSTOM = "custom"


@dataclass
class RecurrenceSpec:
    """Holds specifications for building a recurrence pattern"""

    interval: Optional[DecimalTimeLength] = None
    weekdays: Optional[Set[int]] = None
    times: Optional[Set[str]] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    except_times: Optional[List[tuple[str, str]]] = None


@dataclass
class Modifier:
    func: ModifierFunc
    description: str


@dataclass
class Constraint:
    func: ConstraintFunc
    description: str


class RecurrencePatternProtocol(Protocol):
    """Protocol defining what a RecurrencePattern must implement"""

    spec: RecurrenceSpec
    modifiers: List[Modifier]
    constraints: List[Constraint]

    def add_modifier(self, func: ModifierFunc, description: str) -> None: ...
    def add_constraint(self, func: ConstraintFunc, description: str) -> None: ...
    def next_occurrence(self, from_time: DecimalTimeStamp) -> DecimalTimeStamp: ...


class BuilderProtocol(Protocol):
    """Protocol for builder classes"""

    pattern: RecurrencePatternProtocol
