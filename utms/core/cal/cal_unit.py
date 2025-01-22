from decimal import Decimal
from typing import List, Optional
from types import FunctionType
import datetime
import time
from hy.models import Expression, Integer, List, String, Symbol

from utms.resolvers import CalendarResolver
from utms.utils import get_day_of_week

_resolver = CalendarResolver()

class CalendarUnit:
    def __init__(self, name, units=None, **kwargs):
        self.name: str = name
        self.units = units
        self.length: Decimal = kwargs.get("length", Decimal(0))
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
                    **self.units
                }
                
                # Create a new function with the updated globals
                func_with_globals = FunctionType(
                    func.__code__, 
                    func_globals,
                    func.__name__,
                    func.__defaults__,
                    func.__closure__
                )

                # Cache the function
                self._func_cache[prop] = func_with_globals

                print(args, kwargs)
            return func_with_globals(timestamp, *args, **kwargs)
        elif isinstance(value, (int, float, str, Decimal, list)):
            return value
        else:
            return _resolver.resolve_unit_property(value, self.units, self, timestamp)

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
