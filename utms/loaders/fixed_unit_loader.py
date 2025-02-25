# import os
# from typing import Any, Dict, List, Optional

# import hy

# from ..core.units import Unit
# from ..resolvers import FixedUnitResolver, HyNode, HyResolver
# from ..utils import get_logger
# from ..utms_types import (
#     ExpressionList,
#     HyExpression,
#     HyProperty,
#     LocalsDict,
#     ResolvedValue,
#     UnitConfig,
# )

# logger = get_logger("core.unit.fixed_unit_loader")

# _resolver = FixedUnitResolver()

# def parse_fixed_unit_definitions(nodes: List[HyNode]) -> Dict[str, dict]:
#     """Parse AST nodes into unit specifications."""
#     units = {}
#     logger.debug("Starting to parse unit definitions")

#     for node in nodes:
#         if node.type != "def-fixed-unit":
#             logger.debug(f"Skipping non-unit node: {node.type}")
#             continue

#         unit_label = node.value
#         logger.debug(f"Processing unit: {unit_label}")

#         unit_kwargs_dict = {}
#         for prop in node.children:
#             if prop.type == "property":
#                 prop_name = prop.value
#                 if prop.children:
#                     prop_value = prop.children[0].value
#                     unit_kwargs_dict[prop_name] = prop_value
#                     logger.debug(f"Added property {prop_name}: {prop_value}")

#         units[unit_label] = {"label": unit_label, "kwargs": unit_kwargs_dict}
#         logger.info(f"Added unit {unit_label}")

#     return units

# def initialize_fixed_units(parsed_units: Dict[str, Any], variables: Dict[str, Any] = None) -> Dict[str, Unit]:
#     """Initialize Unit objects from definitions."""
#     units = {}
#     for label, definition in parsed_units.items():
#         # Resolve properties using resolver
#         resolved_props = _resolver.resolve_unit_property(definition["kwargs"], variables=variables)

#         config = UnitConfig(
#             label=label,
#             name=resolved_props.get("name"),
#             value=resolved_props.get("value"),
#             groups=resolved_props.get("groups", [])
#         )

#         units[label] = Unit(config)

#     return units

# def process_fixed_units(unit_data: ExpressionList) -> dict:
#     """Process Hy unit definitions into fully initialized units."""
#     logger.debug("Starting process_units")
#     parsed_units = parse_fixed_unit_definitions(unit_data)
#     logger.debug("Parsed units: %s", list(parsed_units.keys()))
#     units = initialize_fixed_units(parsed_units)
#     logger.debug("Initialized units: %s", list(units.keys()))
#     return units
