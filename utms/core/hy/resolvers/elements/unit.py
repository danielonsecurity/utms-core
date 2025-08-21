from decimal import Decimal
from typing import Any, Dict, Optional, TYPE_CHECKING

from utms.core.hy.resolvers.base import HyResolver
if TYPE_CHECKING:
    from utms.utms_types import (
        Context,
        DynamicExpressionInfo,
        ExpressionResolver,
        HyDict,
        HyExpression,
        HyKeyword,
        HyList,
        HySymbol,
        HyValue,
        LocalsDict,
        LocalsProvider,
        ResolvedValue,
    )


class UnitResolver(HyResolver):
    def get_locals_dict(self, context: "Context", local_names: "LocalsDict" = None) -> "LocalsDict":
        locals_dict = {}

        if context:
            locals_dict["self"] = context
            self.logger.debug("Added self: %s", context)

        if local_names:
            locals_dict.update(local_names)
            self.logger.debug("Added local names: %s", list(local_names.keys()))

        self.logger.debug("Final locals dictionary keys: %s", list(locals_dict.keys()))
        return locals_dict

    def resolve_unit_property(self, expr: dict, unit: Optional[Any] = None, variables=None) -> dict:
        """Resolve all properties in the unit kwargs dictionary"""
        resolved = {}
        local_names = variables if variables else {}
        for key, value in expr.items():
            self.logger.debug("Resolving property %s with value type: %s", key, type(value))
            self.logger.debug("Value: %s", value)
            if isinstance(value, (HyExpression, HyList, HySymbol, HyDict)):
                try:
                    resolved_value = self.resolve(value, unit, local_names)
                    self.logger.debug(
                        "Resolved %s to %s (type: %s)", key, resolved_value, type(resolved_value)
                    )
                    resolved[key] = resolved_value
                except Exception as e:
                    self.logger.error("Error resolving %s: %s", key, e)
            else:
                resolved[key] = value

        return resolved
