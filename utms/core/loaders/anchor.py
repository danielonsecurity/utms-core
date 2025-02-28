from decimal import Decimal
from typing import Any, Dict, List, Optional
from datetime import datetime

import hy

from utms.core.hy.resolvers import AnchorResolver
from utms.core.hy.ast.node import HyNode
from utms.utils import hy_to_python

from ..formats import TimeUncertainty
from ..loaders.base import ComponentLoader, LoaderContext
from ..managers.anchor import AnchorManager
from ..models.anchor import Anchor, FormatSpec

class AnchorLoader(ComponentLoader[Anchor, AnchorManager]):
    """Loader for Anchor components."""

    def __init__(self, manager: AnchorManager):
        super().__init__(manager)
        self._resolver = AnchorResolver()

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
                        # Store both value and original if it's a dynamic expression
                        anchor_props[prop_name] = {
                            "value": value_node.value,
                            "original": value_node.original if value_node.is_dynamic else None,
                        }

            anchors[anchor_label] = {"label": anchor_label, "properties": anchor_props}

        return anchors


    def create_object(self, label: str, properties: Dict[str, Any]) -> Anchor:
        """Create an Anchor from properties."""
        props = properties["properties"]
        resolved_props = self._resolver.resolve_anchor_property(
            props,
            variables=self.context.variables if self.context else None
        )

        # Get name with its original expression
        name_value = props['name']['value']
        name_original = props['name'].get('original')

        # Get value and its original expression
        value = resolved_props['value']['value']
        value_original = props['value'].get('original')


        # Resolve name if it's an expression
        if isinstance(name_value, (hy.models.Expression, hy.models.Symbol)):
            resolved_name = self._resolver.resolve(
                name_value,
                context=None,
                local_names=self.context.variables
            )
        else:
            resolved_name = name_value

        if isinstance(value, (hy.models.Expression, hy.models.Symbol)):
            resolved_value = self._resolver.resolve(
                value,
                context=None,
                local_names=self.context.variables
            )
        else:
            resolved_value = value

        # Convert datetime to timestamp if needed
        if isinstance(resolved_value, datetime):
            resolved_value = resolved_value.timestamp()

        # Create anchor
        anchor = Anchor(
            label=label,
            name=str(resolved_name),
            name_original=name_original,
            value=Decimal(hy_to_python(resolved_value)),
            value_original=value_original,
            formats=[
                FormatSpec(
                    format=str(fmt) if isinstance(fmt, hy.models.String) else None,
                    units=[str(u) for u in fmt] if isinstance(fmt, hy.models.List) else None
                )
                for fmt in resolved_props.get('formats', {}).get('value', [])
            ],
            groups=[str(g) for g in resolved_props.get('groups', {}).get('value', [])],
            uncertainty=self._parse_uncertainty(resolved_props.get('uncertainty', {}))
        )


        return anchor


    def process(self, nodes: List[HyNode], context: LoaderContext) -> Dict[str, Anchor]:
        """Process nodes into Anchors with resolution context."""
        self.context = context
        return super().process(nodes, context)

    def _parse_uncertainty(self, uncertainty_data: Dict) -> Optional[TimeUncertainty]:
        """Parse uncertainty data into TimeUncertainty object."""
        if not uncertainty_data or 'value' not in uncertainty_data:
            return None

        data = uncertainty_data['value']
        if isinstance(data, dict):
            return TimeUncertainty(
                absolute=Decimal(data.get('absolute', '1e-9')),
                relative=Decimal(data.get('relative', '1e-9')),
                confidence_95=data.get('confidence_95')
            )
        return None
    
