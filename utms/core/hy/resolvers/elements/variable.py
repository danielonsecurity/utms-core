import datetime
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
        """Resolve a variable expression"""
        # First, get the result from the parent class
        resolved_value, dynamic_info = super().resolve(expression, context, local_names)
        
        # If this is a named variable (from context), store its resolved value
        if context and 'current_label' in context:
            var_name = context['current_label']
            if isinstance(resolved_value, DynamicExpressionInfo):
                self._resolved_vars[var_name] = resolved_value.latest_value
            else:
                self._resolved_vars[var_name] = resolved_value

        return resolved_value, dynamic_info

    def get_locals_dict(self, context: Context, local_names: LocalsDict = None) -> LocalsDict:
        """Provide config-specific context for Hy evaluation"""
        locals_dict = super().get_locals_dict(context, local_names)


        locals_dict.update({
            "datetime": datetime,
            "time": time,
            "get_ntp_date": get_ntp_date,
            "get_timezone": get_timezone_from_seconds,
            **self._resolved_vars,
        })
        for name, value in self._resolved_vars.items():
            if isinstance(value, DynamicExpressionInfo):
                actual_value = value.latest_value
            else:
                actual_value = value
            locals_dict[name] = actual_value
            locals_dict[name.replace("-", "_")] = actual_value 
        self.logger.debug("Locals dict contains: %s", locals_dict.keys())
        return locals_dict
