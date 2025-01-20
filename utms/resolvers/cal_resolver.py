import datetime
import time

from utms.utils import get_day_of_week

from .hy_resolver import HyResolver


class CalendarResolver(HyResolver):
    def get_locals_dict(self, context, local_names):
        locals_dict = {
            "time": time,
            "datetime": datetime,
            "get_day_of_week": get_day_of_week,
        }

        if context:
            locals_dict["self"] = context
            if hasattr(context, "units"):
                # Create a new dict with units and get_day_of_week
                units_dict = dict(context.units)
                units_dict["get_day_of_week"] = get_day_of_week
                locals_dict.update(units_dict)

        if local_names:
            locals_dict.update(local_names)

        return locals_dict

    def resolve_unit_property(
        self, expr, units, current_unit=None, timestamp=None, local_names=None
    ):
        """Calendar-specific resolution method"""
        return self.resolve(expr, current_unit, local_names)
