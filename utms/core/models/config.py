from dataclasses import dataclass, field
from typing import Any, List, Optional, Union

from utms.core.mixins.model import ModelMixin


@dataclass
class Config(ModelMixin):
    """Represents a configuration entry with its properties."""

    key: str
    value: Any
    is_dynamic: bool = False
    original: Optional[str] = None

    def __post_init__(self):
        # Ensure is_dynamic is set based on original expression
        if self.original is not None:
            self.is_dynamic = True

    def __repr__(self) -> str:
        return (
            f"Config(key={self.key}, "
            f"value={self.value}, "
            f"is_dynamic={self.is_dynamic}, "
            f"original={self.original})"
        )

    def __hash__(self):
        return hash(self.key)

    def __eq__(self, other):
        if not isinstance(other, Config):
            return False
        return self.key == other.key

    def format(self) -> str:
        """
        Format the config value for display.

        This method can be expanded to handle different types of config values.
        """
        if self.is_dynamic and self.original:
            return f"{self.value} (dynamic: {self.original})"
        return str(self.value)
