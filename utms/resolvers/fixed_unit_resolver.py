from decimal import Decimal
from typing import Any, Dict, Optional

from ..utils import get_logger, hy_to_python
from ..utms_types import Context, HyDict, HyExpression, HyList, HySymbol, LocalsDict, ResolvedValue
from .hy_resolver import HyResolver, evaluate_hy_expression

logger = get_logger("resolvers.fixed_unit_resolver")


class FixedUnitResolver(HyResolver):
    def get_locals_dict(self, context: Context, local_names: LocalsDict = None) -> LocalsDict:
        locals_dict = {}

        if context:
            locals_dict["self"] = context
            logger.debug("Added self: %s", context)

        if local_names:
            locals_dict.update(local_names)
            logger.debug("Added local names: %s", list(local_names.keys()))

        logger.debug("Final locals dictionary keys: %s", list(locals_dict.keys()))
        return locals_dict

    def resolve_unit_property(self, expr: dict, unit: Optional[Any] = None, variables=None) -> dict:
        """Resolve all properties in the unit kwargs dictionary"""
        resolved = {}
        local_names = variables if variables else {}
        for key, value in expr.items():
            logger.debug("Resolving property %s with value type: %s", key, type(value))
            logger.debug("Value: %s", value)
            if isinstance(value, (HyExpression, HyList, HySymbol, HyDict)):
                try:
                    resolved_value = self.resolve(value, unit, local_names)
                    logger.debug(
                        "Resolved %s to %s (type: %s)", key, resolved_value, type(resolved_value)
                    )
                    resolved[key] = resolved_value
                except Exception as e:
                    logger.error("Error resolving %s: %s", key, e)
            else:
                resolved[key] = value

        return resolved


# from typing import Any, Dict

# import hy

# from ..utils import get_logger
# from ..utms_types import Context, HyExpression, LocalsDict, ResolvedValue, is_expression
# from .hy_resolver import HyResolver

# logger = get_logger("resolvers.fixed_unit_resolver")


# class FixedUnitResolver:
#     def resolve(self, expr: hy.models.Expression) -> Dict[str, Dict[str, Any]]:
#         if not isinstance(expr, hy.models.Expression):
#             return {}

#         try:
#             if str(expr[0]) == "def-fixed-unit":
#                 unit_label = str(expr[1])
#                 unit_properties = {}
#                 unit_data = {"name": "", "value": "", "groups": []}

#                 # Process each property (name, value, groups)
#                 for prop in expr[2:]:
#                     if isinstance(prop, hy.models.Expression):
#                         prop_name = str(prop[0])
#                         if prop_name == "name":
#                             unit_data["name"] = str(prop[1])
#                         elif prop_name == "value":
#                             unit_data["value"] = str(prop[1])
#                         elif prop_name == "groups":
#                             # Convert Hy list of strings to Python list
#                             unit_data["groups"] = [str(g) for g in prop[1]]

#                 return {unit_label: unit_data}

#         except Exception as e:
#             print(f"Error resolving unit expression: {e}")

#         return {}
