from typing import Optional, Protocol

from ..base.protocols import TimeStamp


class RepeatPattern(Protocol):
    """Protocol for repeat patterns"""

    def next_occurrence(self, from_time: TimeStamp) -> TimeStamp: ...
    def previous_occurrence(self, from_time: TimeStamp) -> TimeStamp: ...
    def is_occurrence(self, timestamp: TimeStamp) -> bool: ...
