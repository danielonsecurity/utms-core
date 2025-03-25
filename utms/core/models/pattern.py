from dataclasses import dataclass, field
from typing import List, Optional

from ..mixins.pattern import PatternMixin


@dataclass
class Pattern(PatternMixin):
    """Represents a recurrence pattern."""

    label: str
    name: str
    every: str
    at: Optional[List[str]] = None
    between: Optional[tuple[str, str]] = None
    on: Optional[List[str]] = None
    except_between: Optional[tuple[str, str]] = None
    groups: List[str] = field(default_factory=list)

    def __post_init__(self):
        if self.groups is None:
            self.groups = []
