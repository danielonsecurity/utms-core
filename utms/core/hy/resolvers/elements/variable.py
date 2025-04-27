from datetime import datetime
import time

from utms.core.hy.resolvers.base import HyResolver
from utms.utils import get_ntp_date, get_timezone_from_seconds
from utms.utms_types import Context, HyExpression, LocalsDict, ResolvedValue, is_expression, DynamicExpressionInfo


class VariableResolver(HyResolver):
    def __init__(self) -> None:
        super().__init__()
        self._resolved_vars = {}

    def resolve(
        self, 
        expression: HyExpression, 
        context: Context = None, 
        local_names: LocalsDict = None
    ) -> tuple[ResolvedValue, DynamicExpressionInfo]:
        """Resolve a variable expression for any field."""
        # First, get the result from the parent class
        resolved_value, dynamic_info = super().resolve(expression, context, local_names)
        
        # If this is a named variable field (from context), store its resolved value
        if context and 'current_label' in context and 'current_field' in context:
            var_name = context['current_label']
            field_name = context['current_field']
            
            # Create a compound key for the field
            field_key = f"{var_name}.{field_name}"
            
            if isinstance(resolved_value, DynamicExpressionInfo):
                self._resolved_vars[field_key] = resolved_value.latest_value
            else:
                self._resolved_vars[field_key] = resolved_value

            self.logger.debug(f"Stored resolved value for {field_key}: {self._resolved_vars[field_key]}")

        return resolved_value, dynamic_info

    def get_locals_dict(self, context: Context, local_names: LocalsDict = None) -> LocalsDict:
        """Provide variable-specific context for Hy evaluation"""
        locals_dict = super().get_locals_dict(context, local_names)

        locals_dict.update({
            "datetime": datetime,
            "time": time,
            "get_ntp_date": get_ntp_date,
            "get_timezone": get_timezone_from_seconds,
            **self._resolved_vars,
        })
        
        # Add all resolved variables to the locals dict
        for name, value in self._resolved_vars.items():
            if isinstance(value, DynamicExpressionInfo):
                actual_value = value.latest_value
            else:
                actual_value = value
                
            # Add both with hyphens and underscores for compatibility
            locals_dict[name] = actual_value
            locals_dict[name.replace("-", "_")] = actual_value
            
            # Also add the field-specific versions if this is a compound key
            if "." in name:
                var_name, field_name = name.split(".", 1)
                if var_name not in locals_dict:
                    locals_dict[var_name] = {}
                if not isinstance(locals_dict[var_name], dict):
                    locals_dict[var_name] = {"value": locals_dict[var_name]}
                locals_dict[var_name][field_name] = actual_value
                
                # Underscore version
                var_name_us = var_name.replace("-", "_")
                field_name_us = field_name.replace("-", "_")
                if var_name_us not in locals_dict:
                    locals_dict[var_name_us] = {}
                if not isinstance(locals_dict[var_name_us], dict):
                    locals_dict[var_name_us] = {"value": locals_dict[var_name_us]}
                locals_dict[var_name_us][field_name_us] = actual_value
        
        self.logger.debug("Locals dict contains: %s", locals_dict.keys())
        return locals_dict
