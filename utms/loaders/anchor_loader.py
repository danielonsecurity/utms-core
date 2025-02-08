import os
from typing import Dict, Optional, List, Any
from ..utils import get_logger, hy_to_python
from ..utms_types import ExpressionList, is_expression, HyExpression, ResolvedValue, LocalsDict, AnchorKwargs
from ..resolvers import AnchorResolver, evaluate_hy_file, HyNode
from ..core.anchors import AnchorConfig, Anchor

logger = get_logger("core.anchor.anchor_loader")

_resolver = AnchorResolver()


def parse_anchor_definitions(nodes: List[HyNode]) -> Dict[str, dict]:
    """Parse AST nodes into anchor specifications."""
    anchors = {}
    logger.debug("Starting to parse anchor definitions")

    for node in nodes:
        if node.type != 'def-anchor':
            logger.debug(f"Skipping non-anchor node: {node.type}")
            continue

        anchor_label = node.value
        logger.debug(f"Processing anchor: {anchor_label}")

        anchor_kwargs_dict = {}
        for prop in node.children:
            if prop.type == 'property':
                prop_name = prop.value
                # Get the value from the first (and should be only) child
                if prop.children:
                    prop_value = prop.children[0].value
                    anchor_kwargs_dict[prop_name] = prop_value
                    logger.debug(f"Added property {prop_name}: {prop_value}")

        anchors[anchor_label] = {
            "label": anchor_label,
            "kwargs": anchor_kwargs_dict
        }
        logger.info(f"Added anchor {anchor_label}")

    logger.debug("Finished parsing anchors")
    return anchors

def initialize_anchors(parsed_anchors, variables) -> dict:
    """Create Anchor instances from parsed definitions."""
    anchors = {}
    for anchor_label, anchor_info in parsed_anchors.items():
        logger.debug("Creating anchor %s with formats %s", anchor_label, parsed_anchors.get("formats"))
        kwargs = anchor_info["kwargs"]
        logger.debug("kwargs before resolution %s", kwargs)
        resolved_props = _resolver.resolve_anchor_property(kwargs, variables = variables)
        logger.debug("resolved_props after resolution %s", resolved_props)
        kwargs = anchor_info["kwargs"]
        config = AnchorConfig(
            label=anchor_label,
            name=resolved_props.get("name"),
            value=resolved_props.get("value"),
            # breakdowns=hy_to_python(resolved_props.get("breakdowns")),
            formats=resolved_props.get("formats"),
            groups=resolved_props.get("groups"),
            precision=resolved_props.get("precision"),
            uncertainty=resolved_props.get("uncertainty"),
        )
        anchor = Anchor(config)
        logger.debug("Created anchor with formats %s", anchor_label, anchor._formats)
        anchors[anchor_label] = anchor
    return anchors

def resolve_anchor_properties(anchors: dict) -> None:
    """Resolve all Hy expressions in anchor properties."""
    for anchor in anchors.values():
        for prop_name, prop_value in anchor.get_all_properties().items():
            if prop_name != "label" and is_hy_compound(prop_value):
                resolved_value = _resolver.resolve_anchor_property(prop_value, anchor)
                anchor.set_property(prop_name, resolved_value)

def process_anchors(anchor_data: ExpressionList) -> dict:
    """Process Hy anchor definitions into fully initialized anchors."""
    logger.debug("Starting process_anchors")
    parsed_anchors = parse_anchor_definitions(anchor_data)
    logger.debug("Parsed anchors: %s", list(parsed_anchors.keys()))
    anchors = initialize_anchors(parsed_anchors)
    logger.debug("Initialized anchors: %s", list(anchors.keys()))
    resolve_anchor_properties(anchors)
    logger.debug("Resolved anchor properties")
    return anchors


