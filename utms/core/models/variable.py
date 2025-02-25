from dataclasses import dataclass
from typing import Any, Optional

from utms.utms_types import HyProperty

from ..mixins.model import ModelMixin


@dataclass
class Variable(ModelMixin):
    """Represents a variable with its value and original expression."""

    name: str
    property: HyProperty

    @property
    def value(self) -> Any:
        return self.property.value

    @property
    def original(self) -> Optional[str]:
        return self.property.original

    def __repr__(self) -> str:
        return f"Variable(name={self.name}, value={self.value}, original={self.original})"
