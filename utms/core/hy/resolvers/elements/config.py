from utms.core.hy.resolvers.base import HyResolver
from utms.utils import hy_to_python
from utms.utms_types import (
    Context,
    DynamicExpressionInfo,
    HyExpression,
    LocalsDict,
    ResolvedValue,
    is_expression,
)


class ConfigResolver(HyResolver):
    def __init__(self) -> None:
        super().__init__()
        self.config_data = {}

    def get_locals_dict(self, context: Context, local_names: LocalsDict = None) -> LocalsDict:
        """Provide config-specific context for Hy evaluation"""
        locals_dict = super().get_locals_dict(context, local_names or {})
        # Add any config-specific globals here if needed
        return locals_dict

    def _resolve_expression(
        self, expr: HyExpression, context: Context, local_names: LocalsDict = None
    ) -> ResolvedValue:
        """Handle custom-set-config specially."""
        if len(expr) > 0 and str(expr[0]) == "custom-set-config":
            self.logger.debug("Found custom-set-config form")
            result = {}
            # Process each setting
            for setting in expr[1:]:
                if is_expression(setting) and len(setting) == 2:
                    key = str(setting[0])
                    value = setting[1]
                    # Resolve the value using the base resolver
                    resolved_value, _ = self.resolve(value, context, local_names)
                    result[key] = resolved_value
            return result

        return super()._resolve_expression(expr, context, local_names)
