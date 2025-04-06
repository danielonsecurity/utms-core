import datetime
import time

from utms.core.hy.resolvers.base import HyResolver
from utms.utils import get_ntp_date, get_timezone_from_seconds
from utms.utms_types import Context, HyExpression, LocalsDict, ResolvedValue, is_expression, DynamicExpressionInfo


class VariableResolver(HyResolver):
    def __init__(self) -> None:
        super().__init__()
        self._resolved_vars = {}

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
            locals_dict[name] = value  # original name with hyphen
            locals_dict[name.replace("-", "_")] = value  # underscore version
        self.logger.debug("Locals dict contains: %s", locals_dict.keys())
        return locals_dict
