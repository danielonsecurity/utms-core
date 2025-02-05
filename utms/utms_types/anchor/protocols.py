from datetime import datetime
from decimal import Decimal
from typing import Dict, Iterator, List, Optional, Protocol, Union, runtime_checkable

from ..unit import FixedUnitManagerProtocol


class AnchorConfigProtocol(Protocol):
    """Protocol defining the interface for anchor configuration."""

    label: str
    name: str
    value: Union[Decimal, datetime]
    breakdowns: Optional[List[List[str]]]
    groups: Optional[List[str]]
    precision: Optional[Decimal]


class AnchorProtocol(Protocol):
    """Protocol defining the interface for Anchor class."""

    @property
    def label(self) -> str: ...

    @property
    def name(self) -> str: ...

    @property
    def value(self) -> Decimal: ...

    @property
    def precision(self) -> Decimal: ...

    @property
    def breakdowns(self) -> List[List[str]]: ...

    @property
    def groups(self) -> List[str]: ...

    def breakdown(self, total_seconds: Decimal, units: FixedUnitManagerProtocol) -> str:
        """Break down duration into multiple unit formats."""
        ...

    def print(self) -> None:
        """Print anchor details."""
        ...

    def _format_breakdown_entry(self, count: Union[int, Decimal], unit: str) -> str:
        """Format a single breakdown entry."""
        ...

    def _calculate_breakdown(
        self, total_seconds: Decimal, breakdown_units: List[str], units: FixedUnitManagerProtocol
    ) -> List[str]:
        """Calculate breakdown for given units."""
        ...


class AnchorManagerProtocol(Protocol):
    """Protocol defining the interface for AnchorManager class."""

    @property
    def units(self) -> FixedUnitManagerProtocol: ...

    def add_anchor(self, anchor_config: AnchorConfigProtocol) -> None:
        """Add new anchor using configuration."""
        ...

    def delete_anchor(self, label: str) -> None:
        """Delete anchor by label."""
        ...

    def get(self, label: str) -> Optional[AnchorProtocol]:
        """Retrieve anchor by label."""
        ...

    def get_label(self, anchor: AnchorProtocol) -> str:
        """Get label for given anchor."""
        ...

    def get_anchors_by_group(self, group_name: str) -> List[AnchorProtocol]:
        """Get anchors by group name."""
        ...

    def get_anchors_from_str(self, input_text: str) -> List[AnchorProtocol]:
        """Parse string and return sorted anchor list."""
        ...

    def print(self, label: Optional[str] = None) -> None:
        """Print anchor details."""
        ...

    def __iter__(self) -> Iterator[AnchorProtocol]: ...

    def __getitem__(self, index: Union[int, str]) -> AnchorProtocol: ...

    def __len__(self) -> int: ...
