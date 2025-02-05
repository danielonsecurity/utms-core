from ..utms_types import Context, HyExpression, LocalsDict, ResolvedValue, is_expression
from .hy_resolver import HyResolver
from ..utils import get_logger

logger = get_logger("resolvers.config_resolver")

class ConfigResolver(HyResolver):
    def __init__(self) -> None:
        super().__init__()
        self.config_data = {}

    def get_locals_dict(self, context: Context, local_names: LocalsDict = None) -> LocalsDict:
        """Provide config-specific context for Hy evaluation"""
        locals_dict = {}

        return locals_dict

    def _resolve_expression(
        self, expr: HyExpression, context: Context, local_names: LocalsDict = None
    ) -> ResolvedValue:
        """Override to handle custom-set-config specially."""
        if len(expr) > 0 and str(expr[0]) == "custom-set-config":
            logger.debug("Found custom-set-config form")
            result = {}
            # Process each setting, skipping the 'quote' wrapper
            for setting in expr[1:]:
                if is_expression(setting) and len(setting) > 1:
                    # Get the actual pair from (quote pair)
                    quoted_pair = setting[1]
                    if is_expression(quoted_pair) and len(quoted_pair) == 2:
                        key = str(quoted_pair[0])
                        value = quoted_pair[1]
                        result[key] = value
            return result
        
        return super()._resolve_expression(expr, context, local_names)


    def resolve_config_property(self, expr: HyExpression, config=None) -> ResolvedValue:
        """Config-specific resolution method"""
        return self.resolve(expr, config)
