import datetime

from utms.utils import get_ntp_date, get_timezone_from_seconds
from utms.core.logger import get_logger
from utms.utms_types import Context, HyExpression, LocalsDict, ResolvedValue, is_expression
from utms.core.hy.resolvers.base import HyResolver

logger = get_logger()


class VariableResolver(HyResolver):
    def __init__(self) -> None:
        super().__init__()
        self._resolved_vars = {}

    def get_locals_dict(self, context: Context, local_names: LocalsDict = None) -> LocalsDict:
        """Provide config-specific context for Hy evaluation"""
        locals_dict = {
            "datetime": datetime,
            "get_ntp_date": get_ntp_date,
            "get_timezone": get_timezone_from_seconds,
            **self._resolved_vars,
        }
        # Add resolved vars with both hyphen and underscore versions
        for name, value in self._resolved_vars.items():
            locals_dict[name] = value  # original name with hyphen
            locals_dict[name.replace("-", "_")] = value  # underscore version
        logger.debug("Locals dict contains: %s", locals_dict.keys())
        return locals_dict
