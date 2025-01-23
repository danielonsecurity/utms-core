import datetime
import time
from decimal import Decimal
from types import FunctionType
from typing import Any, Dict, List, Optional

from utms.resolvers import CalendarResolver
from utms.utils import get_day_of_week
from utms.utms_types import CalendarUnit as CalendarUnitProtocol
from utms.utms_types import TimeUnit

_resolver = CalendarResolver()


class CalendarUnit(CalendarUnitProtocol, TimeUnit):
    def __init__(
        self,
        name: str,
        units: Optional[Dict[str, "CalendarUnit"]] = None,
        **kwargs: Optional[Dict[str, Any]],
    ):
        self.name: str = name
        self.units: Optional[Dict[str, "CalendarUnit"]] = units
        self.length = kwargs.get("length", Decimal(0))
        self.start: Decimal = kwargs.get("start", Decimal(0))
        self.names: Optional[List[str]] = kwargs.get("names", None)
        self.timezone: Decimal = kwargs.get("timezone", Decimal(0))
        self.offset: int = kwargs.get("offset", 0)
        self.index: int = kwargs.get("index", 0)
        self._func_cache = {}

    def get_value(self, prop, timestamp=0, *args, **kwargs):
        value = getattr(self, prop)
        if callable(value):
            if prop in self._func_cache:
                func_with_globals = self._func_cache[prop]
            else:
                func = value
                # Create a new globals dict with all necessary context
                func_globals = {
                    **func.__globals__,
                    "self": self,
                    "datetime": datetime,
                    "time": time,
                    "get_day_of_week": get_day_of_week,
                    **self.units,
                }

                # Create a new function with the updated globals
                func_with_globals = FunctionType(
                    func.__code__, func_globals, func.__name__, func.__defaults__, func.__closure__
                )

                # Cache the function
                self._func_cache[prop] = func_with_globals
            return func_with_globals(timestamp, *args, **kwargs)
        elif isinstance(value, (int, float, str, Decimal, list)):
            return value
        else:
            return _resolver.resolve_unit_property(value, self)

    def calculate_index(self, timestamp):
        """Calculate the index based on timestamp and unit properties"""
        index = self.get_value("index", timestamp)
        names = self.get_value("names")
        length = self.get_value("length", timestamp)
        start = self.get_value("start", timestamp)

        if not index and names and length and start:
            names_len = len(names)
            unit_length = length
            unit_start = start
            if unit_length:
                self.index = int((timestamp - unit_start) / unit_length * names_len)
            else:
                self.index = 0

    def get_start(self, timestamp: float) -> float:
        """Get start time of the current unit."""
        length = float(self.get_value("length", timestamp))
        start = float(self.get_value("start", timestamp))
        timezone = float(self.get_value("timezone", timestamp))

        if length:
            return start + (((timestamp - start + timezone) // length) * length) - timezone
        return start

    def get_end(self, timestamp: float) -> float:
        """Get end time of the current unit."""
        length = float(self.get_value("length", timestamp))
        return self.get_start(timestamp) + length

    def get_next(self, timestamp: float) -> float:
        """Get start time of the next unit."""
        length = float(self.get_value("length", timestamp))
        return self.get_start(timestamp) + length

    def get_previous(self, timestamp: float) -> float:
        """Get start time of the previous unit."""
        length = float(self.get_value("length", timestamp))
        return self.get_start(timestamp) - length

    def get_current(self, timestamp: float) -> float:
        """Get normalized timestamp within current unit."""
        start = self.get_start(timestamp)
        length = float(self.get_value("length", timestamp))
        return timestamp - start if length else 0
