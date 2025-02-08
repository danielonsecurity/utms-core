from .hy_resolver import HyResolver
from ..utils import get_logger, hy_to_python
from ..utms_types import HyExpression, Context, HySymbol, LocalsDict
from typing import Optional, Any

logger = get_logger("resolvers.event_resolver")

class EventResolver(HyResolver):
    def get_locals_dict(self, context: Context, local_names: LocalsDict = None) -> LocalsDict:
        locals_dict = {}
        
        if context:
            locals_dict["self"] = context
            
        if local_names:
            locals_dict.update(local_names)
            
        return locals_dict

    def resolve_event_property(
        self, expr: dict, event: Optional[Any] = None, variables=None
    ) -> dict:
        """Resolve all properties in the event kwargs dictionary"""
        resolved = {}
        local_names = variables if variables else {}
        
        for key, value in expr.items():
            logger.debug("Resolving property %s with value type: %s", key, type(value))
            if isinstance(value, (HyExpression, HySymbol)):
                try:
                    resolved_value = self.resolve(value, event, local_names)
                    resolved[key] = resolved_value
                except Exception as e:
                    logger.error("Error resolving %s: %s", key, e)
            else:
                resolved[key] = value

        return resolved
