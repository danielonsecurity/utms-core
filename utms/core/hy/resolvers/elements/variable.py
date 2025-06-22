import time
from datetime import datetime
from typing import TYPE_CHECKING

from utms.core.hy.resolvers.base import HyResolver
from utms.utils import get_ntp_date, get_timezone_from_seconds
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



class VariableResolver(HyResolver):
    def __init__(self) -> None:
        super().__init__()

    def get_locals_dict(self, context: "Context", local_names: "LocalsDict" = None) -> "LocalsDict":
        """
        Provide variable-specific context for Hy evaluation.
        This resolver's locals_dict will primarily get its context from the `context` parameter
        (which comes from `DynamicResolutionService`).
        """
        locals_dict = super().get_locals_dict(context, local_names)

        utility_functions = {
            "datetime": datetime,
            "time": time,
            "get_ntp_date": get_ntp_date,
            "get_timezone": get_timezone_from_seconds,
        }
        for k, v in utility_functions.items():
            if k not in locals_dict:
                locals_dict[k] = v

        self.logger.debug("Locals dict contains: %s", locals_dict.keys())
        return locals_dict
