from typing import TYPE_CHECKING
from utms.core.hy.resolvers.base import HyResolver
from utms.utils import hy_to_python
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


class ConfigResolver(HyResolver):
    def __init__(self) -> None:
        super().__init__()
        self._resolved_configs = {}

    def resolve(
        self, expression: "HyExpression", context: "Context" = None, local_names: "LocalsDict" = None
    ) -> tuple["ResolvedValue", "DynamicExpressionInfo"]:
        """Resolve a config expression for any field."""
        # First, get the result from the parent class
        resolved_value, dynamic_info = super().resolve(expression, context, local_names)

        # If this is a named config field (from context), store its resolved value
        if context and "current_label" in context and "current_field" in context:
            config_name = context["current_label"]
            field_name = context["current_field"]

            # Create a compound key for the field
            field_key = f"{config_name}.{field_name}"

            if isinstance(resolved_value, DynamicExpressionInfo):
                self._resolved_configs[field_key] = resolved_value.latest_value
            else:
                self._resolved_configs[field_key] = resolved_value

            self.logger.debug(
                f"Stored resolved value for {field_key}: {self._resolved_configs[field_key]}"
            )

        return resolved_value, dynamic_info

    def get_locals_dict(self, context: "Context", local_names: "LocalsDict" = None) -> "LocalsDict":
        """Provide config-specific context for Hy evaluation"""
        locals_dict = super().get_locals_dict(context, local_names or {})

        # Add all resolved configs to the locals dict
        for name, value in self._resolved_configs.items():
            if isinstance(value, DynamicExpressionInfo):
                actual_value = value.latest_value
            else:
                actual_value = value

            # Add both with hyphens and underscores for compatibility
            locals_dict[name] = actual_value
            locals_dict[name.replace("-", "_")] = actual_value

            # Also add the field-specific versions if this is a compound key
            if "." in name:
                config_name, field_name = name.split(".", 1)
                if config_name not in locals_dict:
                    locals_dict[config_name] = {}
                if not isinstance(locals_dict[config_name], dict):
                    locals_dict[config_name] = {"value": locals_dict[config_name]}
                locals_dict[config_name][field_name] = actual_value

                # Underscore version
                config_name_us = config_name.replace("-", "_")
                field_name_us = field_name.replace("-", "_")
                if config_name_us not in locals_dict:
                    locals_dict[config_name_us] = {}
                if not isinstance(locals_dict[config_name_us], dict):
                    locals_dict[config_name_us] = {"value": locals_dict[config_name_us]}
                locals_dict[config_name_us][field_name_us] = actual_value

        self.logger.debug("Locals dict contains: %s", locals_dict.keys())
        return locals_dict

    def _resolve_expression(
        self, expr: "HyExpression", context: "Context", local_names: "LocalsDict" = None
    ) -> "ResolvedValue":
        """Handle custom-set-config specially."""
        from utms.utms_types import is_expression
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
