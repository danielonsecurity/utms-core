breakpoint()
import time
from datetime import datetime

from utms.core.calendar.utils import get_day_of_week
from utms.core.hy.resolvers.base import HyResolver
from utms.utms_types import CalendarUnit as CalendarUnitProtocol
from utms.utms_types import Context, DynamicExpressionInfo, HyExpression, LocalsDict, ResolvedValue


class CalendarResolver(HyResolver):
    def get_additional_globals(self):
        return {
            "get_day_of_week": get_day_of_week,
        }

    def get_locals_dict(self, context: Context, local_names: LocalsDict = None) -> LocalsDict:
        self.logger.debug("\nBuilding locals dictionary")
        self.logger.debug("Context: %s", context)
        self.logger.debug("Initial local_names: %s", local_names)
        locals_dict = {
            "time": time,
            "datetime": datetime,
            "get_day_of_week": get_day_of_week,
        }
        self.logger.debug("Added built-ins: %s", list(locals_dict.keys()))

        if context:
            locals_dict["self"] = context
            self.logger.debug("Added self: %s", context)
            if hasattr(context, "units"):
                # Create a new dict with units and get_day_of_week
                units_dict = dict(context.units)
                units_dict["get_day_of_week"] = get_day_of_week
                locals_dict.update(units_dict)
                self.logger.debug("Added units: %s", list(units_dict.keys()))

        if local_names:
            locals_dict.update(local_names)
            self.logger.debug("Added local names: %s", list(local_names.keys()))

        self.logger.debug("Final locals dictionary keys: %s", list(locals_dict.keys()))
        return locals_dict

    def resolve_unit_property(
        self, expr: HyExpression, current_unit: CalendarUnitProtocol
    ) -> ResolvedValue:
        """Calendar-specific resolution method"""
        return self.resolve(expr, current_unit)
