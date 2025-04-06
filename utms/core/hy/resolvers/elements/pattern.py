from typing import Any, Dict

from utms.utms_types import DynamicExpressionInfo
from utms.core.hy.resolvers.base import HyResolver


class PatternResolver(HyResolver):
    """Resolver for pattern expressions"""

    def get_locals_dict(self, context: Any, local_names: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get local variables for pattern resolution"""
        locals_dict = {"self": context}

        if local_names:
            locals_dict.update(local_names)

        return locals_dict

    def resolve_pattern_property(
        self, expr: dict, pattern: Any = None, variables: Dict[str, Any] = None
    ) -> dict:
        """Resolve all properties in the pattern kwargs dictionary"""
        resolved = {}
        local_names = variables if variables else {}

        for key, value in expr.items():
            self.logger.debug("Resolving property %s with value type: %s", key, type(value))
            try:
                resolved_value = self.resolve(value, pattern, local_names)
                self.logger.debug("Resolved %s to %s", key, resolved_value)
                resolved[key] = resolved_value
            except Exception as e:
                self.logger.error("Error resolving %s: %s", key, e)
                resolved[key] = value

        return resolved
