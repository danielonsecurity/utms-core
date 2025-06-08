from dataclasses import dataclass, field
from typing import Any, Dict

from utms.utms_types.field.types import TypedValue


@dataclass
class LogEntry:
    """
    Represents a single (log-context ...) entry in memory.
    The name of the context is the primary value.
    """

    context_name: str
    attributes: Dict[str, TypedValue] = field(default_factory=dict)
    # We can add a unique ID later if needed
