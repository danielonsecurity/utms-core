# import os
# from typing import Any, Dict, List, Optional

# import hy

# from ..core.anchors import Anchor, AnchorConfig
# from ..resolvers import AnchorResolver, HyNode, HyResolver, evaluate_hy_file
# from ..utils import get_logger, hy_to_python
# from ..utms_types import (
#     AnchorKwargs,
#     ExpressionList,
#     HyExpression,
#     HyProperty,
#     LocalsDict,
#     ResolvedValue,
#     is_expression,
# )

# logger = get_logger("core.anchor.anchor_loader")

# _resolver = AnchorResolver()


# def parse_anchor_definitions(nodes: List[HyNode]) -> Dict[str, dict]:
#     """Parse AST nodes into anchor specifications."""
#     anchors = {}
#     logger.debug("Starting to parse anchor definitions")

#     for node in nodes:
#         if node.type != "def-anchor":
#             logger.debug(f"Skipping non-anchor node: {node.type}")
#             continue

#         anchor_label = node.value
#         logger.debug(f"Processing anchor: {anchor_label}")

#         anchor_kwargs_dict = {}
#         for prop in node.children:
#             if prop.type == "property":
#                 prop_name = prop.value
#                 # Get the value from the first (and should be only) child
#                 if prop.children:
#                     prop_value = prop.children[0].value
#                     anchor_kwargs_dict[prop_name] = prop_value
#                     logger.debug(f"Added property {prop_name}: {prop_value}")

#         anchors[anchor_label] = {"label": anchor_label, "kwargs": anchor_kwargs_dict}
#         logger.info(f"Added anchor {anchor_label}")

#     logger.debug("Finished parsing anchors")
#     return anchors


# def evaluate_with_variables(expr, variables):
#     """Evaluate expression with variables, returning original if evaluation fails."""
#     resolver = HyResolver()
#     try:
#         if isinstance(expr, (hy.models.Expression, hy.models.Symbol)):
#             return resolver.resolve(expr, None, variables)
#         return expr
#     except Exception as e:
#         logger.debug(f"Could not evaluate {expr}: {e}")
#         return expr


# def initialize_anchors(
#     definitions: Dict[str, Any], variables: Dict[str, Any] = None
# ) -> Dict[str, Anchor]:
#     """Initialize Anchor objects from definitions."""
#     anchors = {}
#     for label, definition in definitions.items():
#         kwargs = definition["kwargs"]

#         # Store original expressions before evaluation
#         original_expressions = {}
#         evaluated_kwargs = {}

#         for key, value in kwargs.items():
#             if isinstance(value, (hy.models.Expression, hy.models.Symbol)):
#                 original_expressions[key] = hy.repr(value).strip("'")
#                 evaluated_kwargs[key] = evaluate_with_variables(value, variables)
#             else:
#                 evaluated_kwargs[key] = value
#         # Create config with evaluated values, AnchorConfig will create HyProperties
#         config = AnchorConfig(label=label, **evaluated_kwargs)

#         # Now set the original expressions
#         for key, original in original_expressions.items():
#             if key in config._properties:
#                 config._properties[key].original = original

#         anchors[label] = Anchor(config)

#     return anchors


# def resolve_anchor_properties(anchors: dict) -> None:
#     """Resolve all Hy expressions in anchor properties."""
#     for anchor in anchors.values():
#         for prop_name, prop_value in anchor.get_all_properties().items():
#             if prop_name != "label" and is_hy_compound(prop_value):
#                 resolved_value = _resolver.resolve_anchor_property(prop_value, anchor)
#                 anchor.set_property(prop_name, resolved_value)


# def process_anchors(anchor_data: ExpressionList, variables) -> dict:
#     """Process Hy anchor definitions into fully initialized anchors."""
#     logger.debug("Starting process_anchors")
#     parsed_anchors = parse_anchor_definitions(anchor_data)
#     logger.debug("Parsed anchors: %s", list(parsed_anchors.keys()))
#     anchors = initialize_anchors(parsed_anchors, variables)
#     logger.debug("Initialized anchors: %s", list(anchors.keys()))
#     return anchors
