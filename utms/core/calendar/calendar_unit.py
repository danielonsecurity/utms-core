import datetime
import time
from decimal import Decimal
from types import FunctionType

from utms.resolvers import CalendarResolver
from utms.utils import (
    get_datetime_from_timestamp,
    get_day_of_week,
    get_logger,
    get_timezone_from_seconds,
)
from utms.utms_types import ArbitraryArgs, ArbitraryKwargs
from utms.utms_types import CalendarUnit as CalendarUnitProtocol
from utms.utms_types import (
    DecimalTimeLength,
    DecimalTimeStamp,
    FunctionCache,
    NamesList,
    OptionalUnitKwargs,
    OptionalUnitsDict,
    PropertyDict,
    PropertyValue,
    ResolvedValue,
    TimeStamp,
    UnitAttributes,
    UnitKwargs,
    UnitsDict,
    is_names_list,
    is_number,
    is_timelength,
    is_timestamp,
)

_resolver = CalendarResolver()
logger = get_logger("core.calendar.calendar_unit")


class CalendarUnit(CalendarUnitProtocol):
    class Attributes(UnitAttributes):
        def __init__(self, name: str, kwargs: UnitKwargs):
            self.name = name
            self._values = {
                "length": kwargs.get("length", DecimalTimeStamp(0)),
                "start": kwargs.get("start", DecimalTimeStamp(0)),
                "names": kwargs.get("names"),
                "timezone": kwargs.get("timezone", DecimalTimeStamp(0)),
                "offset": kwargs.get("offset", 0),
                "index": kwargs.get("index", 0),
            }

        def get(self, prop: str) -> ResolvedValue:
            return self._values.get(prop)

        def set(self, prop: str, value: PropertyValue) -> None:
            self._values[prop] = value

        def get_all(self) -> PropertyDict:
            return self._values.copy()

        def __str__(self) -> str:
            """String representation of unit attributes."""
            values = [f"{k}={v}" for k, v in self._values.items() if v is not None]
            return f"Attributes({self.name}, {', '.join(values)})"

        def __repr__(self) -> str:
            """Detailed representation of unit attributes."""
            values = [f"{k}={repr(v)}" for k, v in self._values.items()]
            return f"Attributes(name='{self.name}', values={{{', '.join(values)}}})"

    def __init__(
        self,
        name: str,
        units: OptionalUnitsDict = None,
        kwargs: OptionalUnitKwargs = None,
    ):
        self.name = name
        self._func_cache: FunctionCache = {}
        self._attrs = self.Attributes(name, kwargs or {})
        self.units: UnitsDict = units if units is not None else {}

    def get_value(  # pylint: disable=keyword-arg-before-vararg
        self,
        prop: str,
        timestamp: TimeStamp = DecimalTimeStamp(0),
        *args: ArbitraryArgs,
        **kwargs: ArbitraryKwargs,
    ) -> ResolvedValue:
        """Get the value of a unit property.

        Args:
            prop: Property name to get
            timestamp: Optional timestamp (default: 0)
            *args: Additional positional arguments for property functions
            **kwargs: Additional keyword arguments for property functions

        Note:
            timestamp parameter is placed before *args intentionally to allow both
            simple calls like get_value('prop', 123) and extended calls with
            additional arguments for user-defined functions.
        """
        value = self._attrs.get(prop)

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
                    "get_timezone": get_timezone_from_seconds,
                    "get_datetime_from_timestamp": get_datetime_from_timestamp,
                    **self.units,
                }

                # Create a new function with the updated globals
                func_with_globals = FunctionType(
                    func.__code__, func_globals, func.__name__, func.__defaults__, func.__closure__
                )

                # Cache the function
                self._func_cache[prop] = func_with_globals
            try:
                return func_with_globals(timestamp, *args, **kwargs)
            except TypeError:
                logger.debug("Couldn't convert into proper data types for %s.%s", self.name, prop)
                raise
        if isinstance(value, (int, float, str, Decimal, list)):
            return value
        return _resolver.resolve_unit_property(value, self)

    def get_start(
        self, timestamp: TimeStamp = DecimalTimeStamp(0), **kwargs: ArbitraryKwargs
    ) -> DecimalTimeStamp:
        """Get unit start time with guaranteed TimeStamp return type."""
        try:
            value = self.get_value("start", timestamp, **kwargs)
        except TypeError:
            logger.debug("kwargs for %s.start not accepted: %s", self.name, kwargs)
            value = self.get_value("start", timestamp)
        if isinstance(value, (int, float, Decimal)):
            return DecimalTimeStamp(value)
        if isinstance(value, DecimalTimeStamp):
            return value
        raise TypeError(f"Invalid start value type: {type(value)}")

    def get_length(
        self, timestamp: TimeStamp = DecimalTimeStamp(0), **kwargs: ArbitraryKwargs
    ) -> DecimalTimeLength:
        """Get unit length with guaranteed TimeLength return type."""
        try:
            value = self.get_value("length", timestamp, **kwargs)
        except TypeError:
            logger.debug("kwargs for %s.length not accepted: %s", self.name, kwargs)
            value = self.get_value("length", timestamp)
        if isinstance(value, (int, float, Decimal)):
            return DecimalTimeLength(value)
        if isinstance(value, DecimalTimeLength):
            return value
        raise TypeError(f"Invalid length value type: {type(value)}")

    def get_timezone(
        self, timestamp: TimeStamp = DecimalTimeStamp(0), **kwargs: ArbitraryKwargs
    ) -> DecimalTimeLength:
        """Get timezone offset with guaranteed TimeLength return type."""
        try:
            value = self.get_value("timezone", timestamp, **kwargs)
        except TypeError:
            logger.debug("kwargs for %s.timezone not accepted: %s", self.name, kwargs)
            value = self.get_value("timezone", timestamp)
        if isinstance(value, (int, float, Decimal)):
            return DecimalTimeLength(value)
        if isinstance(value, DecimalTimeLength):
            return value
        raise TypeError(f"Invalid timezone value type: {type(value)}")

    def get_names(
        self, timestamp: TimeStamp = DecimalTimeStamp(0), **kwargs: ArbitraryKwargs
    ) -> NamesList:
        try:
            value = self.get_value("names", timestamp, **kwargs)
        except TypeError:
            logger.debug("kwargs for %s.names not accepted: %s", self.name, kwargs)
            value = self.get_value("names", timestamp)
        if is_names_list(value):
            return value
        return None

    def get_offset(
        self, timestamp: TimeStamp = DecimalTimeStamp(0), **kwargs: ArbitraryKwargs
    ) -> Decimal:
        try:
            value = self.get_value("offset", timestamp, **kwargs)
        except TypeError:
            logger.debug("kwargs for %s.offset not accepted: %s", self.name, kwargs)
            value = self.get_value("offset", timestamp)
        if is_number(value):
            return Decimal(value)
        raise TypeError(f"Invalid offset value type: {type(value)}, should be float")

    def get_index(
        self, timestamp: TimeStamp = DecimalTimeStamp(0), **kwargs: ArbitraryKwargs
    ) -> int:
        try:
            value = self.get_value("index", timestamp, **kwargs)
        except TypeError:
            logger.debug("kwargs for %s.index not accepted: %s", self.name, kwargs)
            value = self.get_value("index", timestamp)
        if isinstance(value, (int)):
            return value
        return 0

    def get_property(self, prop: str) -> PropertyValue:
        return self._attrs.get(prop)

    def set_property(self, prop: str, value: "PropertyValue") -> None:
        return self._attrs.set(prop, value)

    def get_all_properties(self) -> PropertyDict:
        return self._attrs.get_all()

    def calculate_index(self, timestamp: TimeStamp = DecimalTimeStamp(0)) -> None:
        """Calculate the index based on timestamp and unit properties"""
        index = self.get_index(timestamp)
        names = self.get_names()
        length = self.get_length(timestamp)
        if not is_timelength(length):
            logger.error("%s must be a number", length)
            raise ValueError(f"{length} length must be a number")
        start = self.get_start(timestamp)
        if not is_timestamp(start):
            logger.error("%s must be a number, not a %s", start, type(start))
            raise ValueError(f"{start} length must be a number, instead it's {type(start)}")

        if not index and names and length and start:
            if not is_names_list(names):
                logger.error("%s must be a list", names)
                raise ValueError(f"{names} must be a list")

            names_len = len(names)
            unit_length = length
            unit_start = start
            if unit_length:
                self.index = int((timestamp - unit_start) / unit_length * names_len)
            else:
                self.index = 0

    def __str__(self) -> str:
        """String representation of the calendar unit."""
        try:
            values = []
            if hasattr(self, "_attrs") and hasattr(self._attrs, "_values"):
                for k, v in self._attrs._values.items():
                    if v is not None:
                        values.append(f"{k}={v}")

            if values:
                return f"CalendarUnit({self.name}, {', '.join(values)})"
            return f"CalendarUnit({self.name})"
        except (AttributeError, KeyError) as e:
            return f"CalendarUnit({self.name}, error='{e.__class__.__name__}: {str(e)}')"

    def __repr__(self) -> str:
        """Detailed representation of the calendar unit."""
        try:
            # Get basic attributes
            attrs = [
                f"name={repr(self.name)}",
                f"units={repr(list(self.units.keys()) if self.units else [])}",
            ]

            # Add values from _attrs if they exist
            if hasattr(self, "_attrs") and hasattr(self._attrs, "_values"):
                for k, v in self._attrs._values.items():
                    attrs.append(f"{k}={repr(v)}")

            # Add any other instance attributes
            for k, v in self.__dict__.items():
                if k not in ("name", "units", "_attrs"):
                    attrs.append(f"{k}={repr(v)}")

            return f"CalendarUnit({', '.join(attrs)})"
        except (AttributeError, KeyError) as e:
            return f"CalendarUnit({self.name}, error='{e.__class__.__name__}: {str(e)}')"

    @property
    def length(self) -> PropertyValue:
        return self._attrs.get("length")

    @length.setter
    def length(self, value: PropertyValue) -> None:
        self._attrs.set("length", value)

    @property
    def start(self) -> PropertyValue:
        return self._attrs.get("start")

    @start.setter
    def start(self, value: PropertyValue) -> None:
        self._attrs.set("start", value)

    @property
    def names(self) -> PropertyValue:
        return self._attrs.get("names")

    @names.setter
    def names(self, value: PropertyValue) -> None:
        self._attrs.set("names", value)

    @property
    def timezone(self) -> PropertyValue:
        return self._attrs.get("timezone")

    @timezone.setter
    def timezone(self, value: PropertyValue) -> None:
        self._attrs.set("timezone", value)

    @property
    def offset(self) -> PropertyValue:
        return self._attrs.get("offset")

    @offset.setter
    def offset(self, value: PropertyValue) -> None:
        self._attrs.set("offset", value)

    @property
    def index(self) -> PropertyValue:
        return self._attrs.get("index")

    @index.setter
    def index(self, value: PropertyValue) -> None:
        self._attrs.set("index", value)
