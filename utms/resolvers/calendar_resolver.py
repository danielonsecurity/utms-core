import datetime
import time

from utms.utils import get_day_of_week, get_logger

from .hy_resolver import HyResolver

logger = get_logger("resolvers.calendar_resolver")

class CalendarResolver(HyResolver):
    def get_locals_dict(self, context, local_names):
        logger.debug("\nBuilding locals dictionary")
        logger.debug(f"Context: {context}")
        logger.debug(f"Initial local_names: {local_names}")
        locals_dict = {
            "time": time,
            "datetime": datetime,
            "get_day_of_week": get_day_of_week,
        }
        logger.debug(f"Added built-ins: {list(locals_dict.keys())}")

        if context:
            locals_dict["self"] = context
            logger.debug(f"Added self: {context}")
            if hasattr(context, "units"):
                # Create a new dict with units and get_day_of_week
                units_dict = dict(context.units)
                units_dict["get_day_of_week"] = get_day_of_week
                locals_dict.update(units_dict)
                logger.debug(f"Added units: {list(units_dict.keys())}")

        if local_names:
            locals_dict.update(local_names)
            logger.debug(f"Added local names: {list(local_names.keys())}")

        logger.debug(f"Final locals dictionary keys: {list(locals_dict.keys())}")
        return locals_dict

    def resolve_unit_property(
        self, expr, units, current_unit=None, timestamp=None, local_names=None
    ):
        """Calendar-specific resolution method"""
        return self.resolve(expr, current_unit, local_names)
