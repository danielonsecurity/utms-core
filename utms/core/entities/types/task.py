from enum import Enum
from typing import ClassVar, Dict

from utms.utms_types.entity.attributes import CORE_ATTRIBUTES, EXTENDED_ATTRIBUTES
from utms.utms_types.entity.types import AttributeDefinition

from ..base import TimeEntity


class TaskState(str, Enum):
    """Basic task states"""

    TODO = "TODO"
    NEXT = "NEXT"
    DONE = "DONE"
    CANCELLED = "CANCELLED"


class Task(TimeEntity):
    """A task entity with state and time specifications"""

    attributes: ClassVar[Dict[str, AttributeDefinition]] = {
        **CORE_ATTRIBUTES,
        "state": AttributeDefinition(str, default=TaskState.TODO),
        "completion_history": EXTENDED_ATTRIBUTES["completion_history"],
        "time_tracking": EXTENDED_ATTRIBUTES["time_tracking"],
        "clock_entries": EXTENDED_ATTRIBUTES["clock_entries"],
        "description": EXTENDED_ATTRIBUTES["description"],
    }

    def __init__(self, name: str):
        super().__init__(name)
        self.state = TaskState.TODO  # Use direct attribute assignment

    def mark_done(self) -> None:
        """Mark the task as done"""
        self.state = TaskState.DONE

    def mark_cancelled(self) -> None:
        """Mark the task as cancelled"""
        self.state = TaskState.CANCELLED

    def mark_next(self) -> None:
        """Mark the task as next action"""
        self.state = TaskState.NEXT

    def is_done(self) -> bool:
        """Check if task is completed"""
        return self.state == TaskState.DONE

    def is_cancelled(self) -> bool:
        """Check if task is cancelled"""
        return self.state == TaskState.CANCELLED

    def is_active(self) -> bool:
        """Check if task is active (not done or cancelled)"""
        return not (self.is_done() or self.is_cancelled())
