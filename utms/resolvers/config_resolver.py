from .hy_resolver import HyResolver


class ConfigResolver(HyResolver):
    def get_locals_dict(self, context, local_names):
        """Provide config-specific context for Hy evaluation"""
        locals_dict = {}

        # Add any config-specific functions or variables needed
        if context:
            locals_dict["self"] = context
            # Add any config-specific context here

        if local_names:
            locals_dict.update(local_names)

        return locals_dict

    def resolve_config_property(self, expr, config=None, local_names=None):
        """Config-specific resolution method"""
        return self.resolve(expr, config, local_names)
