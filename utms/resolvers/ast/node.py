from dataclasses import dataclass
from typing import Any, List, Optional

@dataclass
class HyNode:
    """A node in the Hy AST."""
    type: str  # 'def-anchor', 'def-event', 'property', 'value', 'comment'
    value: Any  # The actual value/content
    children: Optional[List["HyNode"]] = None
    comment: Optional[str] = None  # Associated comment if any
    original: Any = None  # Original Hy expression
    is_dynamic: bool = False

    def __post_init__(self):
        self.children = self.children or []
