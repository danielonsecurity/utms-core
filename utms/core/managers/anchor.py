from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

from utms.utils import format_value
from utms.utms_types import AnchorManagerProtocol

from ..formats import TimeUncertainty
from ..models.anchor import Anchor, FormatSpec
from .base import BaseManager


class AnchorManager(BaseManager[Anchor], AnchorManagerProtocol):
    """Manages anchors with their properties and relationships."""

    def create(
        self,
        label: str,
        name: str,
        value: Union[str, Decimal],
        formats: Optional[List[FormatSpec]] = None,
        groups: Optional[List[str]] = None,
        uncertainty: Optional[TimeUncertainty] = None,
    ) -> Anchor:
        """Create a new anchor."""
        if label in self._items:
            raise ValueError(f"Anchor with label '{label}' already exists")

        anchor = Anchor(
            label=label,
            name=name,
            value=Decimal(value),
            formats=formats or [],
            groups=groups or [],
            uncertainty=uncertainty,
        )

        self.add(label, anchor)
        self._sort_anchors()
        return anchor

    def _sort_anchors(self) -> None:
        """Sort the anchors by their value."""
        breakpoint()
        self._items = dict(sorted(self._items.items(), key=lambda item: item[1].value))

    def get_anchors_by_group(self, group: str) -> List[Anchor]:
        """Get all anchors belonging to a specific group."""
        return [anchor for anchor in self._items.values() if group in anchor.groups]

    def get_anchors_by_groups(self, groups: List[str], match_all: bool = False) -> List[Anchor]:
        """Get anchors belonging to multiple groups."""
        if match_all:
            return [
                anchor
                for anchor in self._items.values()
                if all(group in anchor.groups for group in groups)
            ]
        else:
            return [
                anchor
                for anchor in self._items.values()
                if any(group in anchor.groups for group in groups)
            ]

    def serialize(self) -> Dict[str, Dict[str, Any]]:
        """Convert anchors to serializable format."""
        return {
            label: {
                "name": anchor.name,
                "value": str(anchor.value),
                "formats": [
                    {"units": f.units, "style": f.style, "format": f.format, "options": f.options}
                    for f in anchor.formats
                ],
                "groups": anchor.groups,
                "uncertainty": (
                    {
                        "absolute": str(anchor.uncertainty.absolute),
                        "relative": str(anchor.uncertainty.relative),
                        "confidence_95": anchor.uncertainty.confidence_95,
                    }
                    if anchor.uncertainty
                    else None
                ),
            }
            for label, anchor in self._items.items()
        }

    def deserialize(self, data: Dict[str, Dict[str, Any]]) -> None:
        """Load anchors from serialized data."""
        self.clear()
        for label, anchor_data in data.items():
            formats = [
                FormatSpec(
                    units=f.get("units"),
                    style=f.get("style", "default"),
                    format=f.get("format"),
                    options=f.get("options", {}),
                )
                for f in anchor_data.get("formats", [])
            ]

            uncertainty_data = anchor_data.get("uncertainty")
            uncertainty = None
            if uncertainty_data:
                uncertainty = TimeUncertainty(
                    absolute=Decimal(uncertainty_data["absolute"]),
                    relative=Decimal(uncertainty_data["relative"]),
                    confidence_95=uncertainty_data.get("confidence_95"),
                )

            self.create(
                label=label,
                name=anchor_data["name"],
                value=anchor_data["value"],
                formats=formats,
                groups=anchor_data.get("groups", []),
                uncertainty=uncertainty,
            )
