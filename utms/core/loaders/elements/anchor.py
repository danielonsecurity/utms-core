from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

import hy

from utms.core.hy.resolvers import AnchorResolver
from utms.utils import hy_to_python
from utms.utms_types import HyNode

from utms.core.formats import TimeUncertainty
from utms.core.loaders.base import ComponentLoader, LoaderContext
from utms.core.managers.elements.anchor import AnchorManager
from utms.core.models import Anchor, FormatSpec
from utms.core.services.dynamic import DynamicResolutionService


class AnchorLoader(ComponentLoader[Anchor, AnchorManager]):
    """Loader for Anchor components."""

    def __init__(self, manager: AnchorManager):
        super().__init__(manager)
        self._resolver = AnchorResolver()
        self._dynamic_service = DynamicResolutionService()


    def parse_definitions(self, nodes: List[HyNode]) -> Dict[str, dict]:
        """Parse HyNodes into anchor definitions."""
        anchors = {}

        for node in nodes:
            if not self.validate_node(node, "def-anchor"):
                continue

            anchor_label = node.value
            anchor_props = {}

            for prop in node.children:
                if prop.type == "property":
                    prop_name = prop.value
                    if prop.children:
                        value_node = prop.children[0]
                        anchor_props[prop_name] = {
                            "value": value_node.value,
                            "is_dynamic": value_node.is_dynamic,
                            "original": value_node.original if value_node.is_dynamic else None,
                        }

            anchors[anchor_label] = {"label": anchor_label, "properties": anchor_props}

        return anchors

    def create_object(self, label: str, properties: Dict[str, Any]) -> Anchor:
        """Create an Anchor from properties."""
        props = properties["properties"]
        resolved_props = {}

        # Resolve all properties uniformly
        for prop_name, prop_data in props.items():
            value = prop_data["value"]
            is_dynamic = prop_data.get("is_dynamic", False)
            original = prop_data.get("original")

            self.logger.debug(f"Resolving anchor {label} property {prop_name}: {value}")

            if is_dynamic:
                resolved_value, _ = self._dynamic_service.evaluate(
                    component_type='anchor',
                    component_label=label,
                    attribute=prop_name,
                    expression=value,
                    context=self.context.variables if self.context else None
                )
                self.logger.debug(f"Resolved dynamic value for {prop_name}: {resolved_value}")
            else:
                resolved_value = value
                self.logger.debug(f"Using static value for {prop_name}: {resolved_value}")

            resolved_props[prop_name] = {
                "value": resolved_value,
                "is_dynamic": is_dynamic,
                "original": original
            }

        # Convert specific types as needed
        if isinstance(resolved_props["value"]["value"], datetime):
            resolved_props["value"]["value"] = resolved_props["value"]["value"].timestamp()

        # Create anchor with resolved properties
        anchor = Anchor(
            label=label,
            name=str(resolved_props["name"]["value"]),
            name_original=resolved_props["name"].get("original"),
            value=Decimal(hy_to_python(resolved_props["value"]["value"])),
            value_original=resolved_props["value"].get("original"),
            formats=[
                FormatSpec(
                    format=str(fmt) if isinstance(fmt, hy.models.String) else None,
                    units=[str(u) for u in fmt] if isinstance(fmt, hy.models.List) else None,
                )
                for fmt in resolved_props.get("formats", {}).get("value", [])
            ],
            groups=[str(g) for g in resolved_props.get("groups", {}).get("value", [])],
            uncertainty=self._parse_uncertainty(resolved_props.get("uncertainty", {})),
        )

        return anchor

    def _parse_uncertainty(self, uncertainty_data: Dict) -> Optional[TimeUncertainty]:
        """Parse uncertainty data into TimeUncertainty object."""
        if not uncertainty_data or "value" not in uncertainty_data:
            return None

        data = uncertainty_data["value"]
        if isinstance(data, dict):
            return TimeUncertainty(
                absolute=Decimal(data.get("absolute", "1e-9")),
                relative=Decimal(data.get("relative", "1e-9")),
                confidence_95=data.get("confidence_95"),
            )
        return None
