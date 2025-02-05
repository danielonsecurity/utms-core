from typing import Any, List, Optional, Protocol, Union

from ..anchor.protocols import AnchorManagerProtocol
from ..unit.protocols import FixedUnitManagerProtocol


class ConfigProtocol(Protocol):
    """Protocol defining the interface for Config class."""

    @property
    def utms_dir(self) -> str: ...

    @property
    def data(self) -> Any: ...

    @property
    def units(self) -> FixedUnitManagerProtocol: ...

    @property
    def anchors(self) -> AnchorManagerProtocol: ...

    def init_resources(self) -> None:
        """Initialize and copy resources to user config directory."""

    def load(self) -> Any:
        """Load configuration from JSON file."""

    def save(self) -> None:
        """Save configuration to JSON file."""

    def load_anchors(self) -> None:
        """Load anchors from anchors.json file."""

    def save_anchors(self) -> None:
        """Save anchors to anchors.json file."""

    def load_units(self) -> None:
        """Load units from units.json file."""

    def save_units(self) -> None:
        """Save units to units.json file."""

    def get_value(self, key: str, pretty: bool = False) -> Union[Any, str]:
        """Get value from configuration by key."""

    def has_value(self, key: str) -> bool:
        """Check if key exists and has non-None value."""

    def set_value(self, key: str, value: Any) -> None:
        """Set value in configuration by key."""

    def print(self, filter_key: Optional[str] = None) -> None:
        """Print configuration in formatted JSON style."""

    def select_from_choices(self, key: str) -> Any:
        """Allow interactive selection from choices."""

    def select_from_list(self, source_key: str, target_key: str, index: int) -> None:
        """Assign element from JSON array to target key."""

    def select_from_list_interactive(self, source_key: str, target_key: str) -> None:
        """Interactive selection from JSON array."""

    def populate_dynamic_anchors(self) -> None:
        """Populate AnchorManager with dynamic datetime anchors."""

    def _parse_key(self, key: str) -> List[Union[str, int]]:
        """Parse dot-separated key with array indices."""

    def _traverse(self, key: str) -> tuple[Any, Union[str, int]]:
        """Traverse configuration using parsed key."""
