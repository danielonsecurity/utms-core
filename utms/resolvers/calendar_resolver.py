import datetime
import time

from ..utils import get_day_of_week, get_logger
from ..utms_types import CalendarUnit as CalendarUnitProtocol
from ..utms_types import Context, HyExpression, LocalsDict, ResolvedValue
from .hy_resolver import HyResolver

logger = get_logger("resolvers.calendar_resolver")


class CalendarResolver(HyResolver):
    def get_locals_dict(self, context: Context, local_names: LocalsDict = None) -> LocalsDict:
        logger.debug("\nBuilding locals dictionary")
        logger.debug("Context: %s", context)
        logger.debug("Initial local_names: %s", local_names)
        locals_dict = {
            "time": time,
            "datetime": datetime,
            "get_day_of_week": get_day_of_week,
        }
        logger.debug("Added built-ins: %s", list(locals_dict.keys()))

        if context:
            locals_dict["self"] = context
            logger.debug("Added self: %s", context)
            if hasattr(context, "units"):
                # Create a new dict with units and get_day_of_week
                units_dict = dict(context.units)
                units_dict["get_day_of_week"] = get_day_of_week
                locals_dict.update(units_dict)
                logger.debug("Added units: %s", list(units_dict.keys()))

        if local_names:
            locals_dict.update(local_names)
            logger.debug("Added local names: %s", list(local_names.keys()))

        logger.debug("Final locals dictionary keys: %s", list(locals_dict.keys()))
        return locals_dict

    def resolve_unit_property(
        self, expr: HyExpression, current_unit: CalendarUnitProtocol
    ) -> ResolvedValue:
        """Calendar-specific resolution method"""
        return self.resolve(expr, current_unit)
