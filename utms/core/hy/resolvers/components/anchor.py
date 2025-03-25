import datetime
from decimal import Decimal
from typing import Any, Optional

from utms.core.formats.config import TimeUncertainty
from utms.core.hy import evaluate_hy_expression, evaluate_hy_file
from utms.core.hy.resolvers.base import HyResolver
from utms.core.mixins import ResolverMixin
from utms.utils import get_ntp_date, hy_to_python
from utms.utms_types import (
    Context,
    HyDict,
    HyExpression,
    HyList,
    HySymbol,
    LocalsDict,
    ResolvedValue,
    is_dict,
)


class AnchorResolver(HyResolver):
    def get_locals_dict(self, context: Context, local_names: LocalsDict = None) -> LocalsDict:
        locals_dict = {
            "datetime": datetime,
            "get_ntp_date": get_ntp_date,
        }

        if context:
            locals_dict["self"] = context
            self.logger.debug("Added self: %s", context)

        if local_names:
            locals_dict.update(local_names)
            self.logger.debug("Added local names: %s", list(local_names.keys()))

        self.logger.debug("Final locals dictionary keys: %s", list(locals_dict.keys()))
        return locals_dict

    def resolve_anchor_property(
        self, expr: dict, anchor: Optional[Any] = None, variables=None
    ) -> dict:
        """Resolve all properties in the anchor kwargs dictionary"""
        resolved = {}
        local_names = variables if variables else {}

        for key, value in expr.items():
            self.logger.debug("Resolving property %s with value type: %s", key, type(value))
            self.logger.debug("Value: %s", value)
            if isinstance(value, (HyExpression, HyList, HySymbol, HyDict)):
                try:
                    resolved_value = self.resolve(value, anchor, local_names)
                    self.logger.debug(
                        "Resolved %s to %s (type: %s)", key, resolved_value, type(resolved_value)
                    )
                    if key == "uncertainty":
                        resolved_value = self._create_uncertainty(resolved_value)

                    resolved[key] = resolved_value
                except Exception as e:
                    self.logger.error("Error resolving %s: %s", key, e)
            else:
                resolved[key] = value

        return resolved

    def _create_uncertainty(self, resolved_value: dict) -> TimeUncertainty:
        absolute = Decimal("1")  # default
        relative = Decimal("0")  # default
        confidence_95 = None

        py_resolved_value = hy_to_python(resolved_value)

        if is_dict(resolved_value):
            if "absolute" in py_resolved_value:
                index = py_resolved_value.index("absolute")
                absolute = Decimal(py_resolved_value[index + 1])
            if "relative" in py_resolved_value:
                index = py_resolved_value.index("relative")
                relative = Decimal(py_resolved_value[index + 1])
            if "confidence_95" in py_resolved_value:
                index = py_resolved_value.index("confidence_95")
                conf = py_resolved_value[index + 1]
                if isinstance(conf, (list, tuple)) and len(conf) == 2:
                    confidence_95 = (Decimal(str(conf[0])), Decimal(str(conf[1])))

        return TimeUncertainty(absolute=absolute, relative=relative, confidence_95=confidence_95)
