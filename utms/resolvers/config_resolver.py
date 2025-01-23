from ..utms_types import Context, HyExpression, LocalsDict, ResolvedValue
from .hy_resolver import HyResolver


class ConfigResolver(HyResolver):
    def get_locals_dict(self, context: Context, local_names: LocalsDict = None) -> LocalsDict:
        """Provide config-specific context for Hy evaluation"""
        locals_dict = {}

        # Add any config-specific functions or variables needed
        if context:
            locals_dict["self"] = context
            # Add any config-specific context here

        if local_names:
            locals_dict.update(local_names)

        return locals_dict

    def resolve_config_property(self, expr: HyExpression, config=None) -> ResolvedValue:
        """Config-specific resolution method"""
        return self.resolve(expr, config)
