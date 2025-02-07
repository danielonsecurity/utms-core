import os
from typing import Dict, Optional
from ..utils import get_logger, hy_to_python
from ..utms_types import ExpressionList, is_expression, HyExpression, ResolvedValue, LocalsDict, AnchorKwargs
from ..resolvers import AnchorResolver, evaluate_hy_file
from ..core.anchors import AnchorConfig, Anchor

logger = get_logger("core.anchor.anchor_loader")

_resolver = AnchorResolver()

def parse_anchor_definitions(anchor_data: ExpressionList) -> Dict[str, dict]:
    """Parse Hy anchor definitions into a dictionary of anchor specifications."""
    anchors = {}
    logger.debug("Starting to parse anchor definitions")

    for anchor_def_expr in anchor_data:
        if not is_expression(anchor_def_expr):
            logger.debug("Skipping non-Expression: %s", anchor_def_expr)
            continue

        if str(anchor_def_expr[0]) != "def-anchor":
            logger.debug("Skipping non-def-anchor expression: %s", anchor_def_expr[0])
            continue

        _, anchor_label_sym, *anchor_properties = anchor_def_expr
        anchor_label = str(anchor_label_sym)
        logger.debug("Processing anchor: %s", anchor_label)

        anchor_kwargs_dict = {}
        for prop_expr in anchor_properties:
            if is_expression(prop_expr):
                prop_name = str(prop_expr[0])
                prop_value = prop_expr[1]
                anchor_kwargs_dict[prop_name] = prop_value
            else:
                logger.error("Unexpected item type in anchor properties %s", type(prop_expr))
                raise ValueError(f"Unexpected item type in anchor properties {type(prop_expr)}")
        # anchor_kwargs = AnchorKwargs(
        #     name=anchor_kwargs_dict.get("name"),
        #     value=anchor_kwargs_dict.get("value"),
        #     groups=anchor_kwargs_dict.get("groups"),
        #     precision=anchor_kwargs_dict.get("precision"),
        #     breakdowns=anchor_kwargs_dict.get("breakdowns"),
        # )
        anchors[anchor_label] = {
            "label": anchor_label,
            "kwargs": anchor_kwargs_dict
        }
        logger.info("Added anchor %s", anchor_label)
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


