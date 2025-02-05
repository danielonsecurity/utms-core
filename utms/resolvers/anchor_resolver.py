import datetime
from .hy_loader import evaluate_hy_file
from .hy_resolver import HyResolver, evaluate_hy_expression
from ..utils import get_logger, hy_to_python, get_ntp_date
from ..utms_types import HyExpression, Context, HySymbol, LocalsDict, ResolvedValue, HyList
from typing import Optional, Any


logger = get_logger("core.config")

class AnchorResolver(HyResolver):
    def get_locals_dict(self, context: Context, local_names: LocalsDict = None) -> LocalsDict:
        locals_dict = {
            "datetime": datetime,
            "get_ntp_date": get_ntp_date,
        }
        
        if context:
            locals_dict["self"] = context
            logger.debug("Added self: %s", context)

        if local_names:
            locals_dict.update(local_names)
            logger.debug("Added local names: %s", list(local_names.keys()))

        logger.debug("Final locals dictionary keys: %s", list(locals_dict.keys()))
        return locals_dict



    def resolve_anchor_property(
        self, expr: dict, anchor: Optional[Any] = None, variables=None
    ) -> dict:
        """Resolve all properties in the anchor kwargs dictionary"""
        resolved = {}
        local_names = variables if variables else {}
        
        for key, value in expr.items():
            logger.debug("Resolving property %s with value type: %s", key, type(value))
            logger.debug("Value: %s", value)
            if isinstance(value, (HyExpression, HyList, HySymbol)):
                try:
                    resolved_value = self.resolve(value, anchor, local_names)
                    logger.debug("Resolved %s to %s (type: %s)", key, resolved_value, type(resolved_value))
                    resolved[key] = resolved_value
                except Exception as e:
                    logger.error("Error resolving %s: %s", key, e)
            else:
                resolved[key] = value

        return resolved
