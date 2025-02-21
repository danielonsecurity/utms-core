from enum import Enum
from dataclasses import dataclass
from typing import Callable, List, Optional, Set, Union
from utms.utms_types.base.time import DecimalTimeStamp, DecimalTimeLength

# Type aliases for function signatures
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
