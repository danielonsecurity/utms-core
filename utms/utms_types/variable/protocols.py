from typing import Any, Dict, Iterator, List, Optional, Protocol, Union


class VariableProtocol(Protocol):
    """Protocol defining the interface for Variable class."""

    @property
    def key(self) -> str: ...

    @property
    def value(self) -> Any: ...

    @property
    def is_dynamic(self) -> bool: ...

    @property
    def original(self) -> Optional[str]: ...

    def format(self) -> str:
        """Format the variable value for display."""
        ...


class VariableManagerProtocol(Protocol):
    """Protocol defining the interface for VariableManager class."""

    def create(
        self,
        key: str,
        value: Any,
        is_dynamic: bool = False,
        original: Optional[str] = None,
    ) -> "VariableProtocol":
        """Create a new variable entry."""
        ...

    def get(self, key: str) -> Optional["VariableProtocol"]:
        """Retrieve variable by key."""
        ...

    def remove(self, key: str) -> Optional["VariableProtocol"]:
        """Remove variable by key."""
        ...

    def get_variables_by_type(self, is_dynamic: bool) -> List["VariableProtocol"]:
        """Get variables filtered by dynamic status."""
        ...

    def get_variables_by_prefix(self, prefix: str) -> List["VariableProtocol"]:
        """Get variables with keys starting with a specific prefix."""
        ...

    def serialize(self) -> Dict[str, Dict[str, Any]]:
        """Convert variables to serializable format."""
        ...

    def deserialize(self, data: Dict[str, Dict[str, Any]]) -> None:
        """Load variables from serialized data."""
        ...

    def __iter__(self) -> Iterator["VariableProtocol"]:
        """Iterate over all variables."""
        ...

    def __getitem__(self, key: str) -> "VariableProtocol":
        """Dictionary-style access to variables."""
        ...

    def __len__(self) -> int:
        """Get number of variables."""
        ...

    def __contains__(self, key: str) -> bool:
        """Check if a variable key exists."""
        ...
