import datetime
import time
from types import FunctionType
from typing import Optional

from utms.resolvers import CalendarResolver, evaluate_hy_expression
from utms.utils import (
    ColorFormatter,
    TimeRange,
    get_datetime_from_timestamp,
    get_day_of_week,
    get_logger,
    get_timezone_from_seconds,
)
from utms.utms_types import HyExpression

from .calendar_calculator import MonthCalculator, YearCalculator
from .calendar_data import CalendarState, MonthData
from .calendar_display import (
    DayContext,
    DayFormatter,
    MonthHeaderFormatter,
    WeekContext,
    WeekdayHeaderFormatter,
    WeekRowFormatter,
    YearContext,
    YearHeaderFormatter,
)
from .calendar_printer import CalendarPrinter, PrinterContext
from .registry import CalendarRegistry

_resolver = CalendarResolver()
logger = get_logger("core.calendar.calendar")


class Calendar:
    def __init__(self, name, timestamp):
        logger.debug("Initializing calendar %s", name)
        self.name = name
        self.timestamp = timestamp
        self.units = CalendarRegistry.get_calendar_units(name)

        self._state = self._create_calendar_state()
        self._printer = self._create_printer()
        self._year_calculator = YearCalculator()
        self._month_calculator = MonthCalculator()

        self._func_cache = {}

        logger.info(f"Calendar '{name}' initialized successfully")

    def _create_calendar_state(self) -> CalendarState:
        """Create initial calendar state."""
        week_length = self.week_unit.get_value("length", self.timestamp) // self.day_unit.get_value(
            "length", self.timestamp
        )
        today_start = self.day_unit.get_value("start", self.timestamp)
        current_week_range = self.get_time_range(self.timestamp, self.week_unit)
        current_month_range = self.get_time_range(self.timestamp, self.month_unit)

        return CalendarState(
            name=self.name,
            timestamp=self.timestamp,
            week_length=week_length,
            today_start=today_start,
            current_week_range=current_week_range,
            current_month_range=current_month_range,
            units=self.units,
        )

    def _create_printer(self) -> CalendarPrinter:
        """Create printer with appropriate context."""
        printer_context = PrinterContext(
            week_length=self._state.week_length,
            current_week_range=self._state.current_week_range,
            current_month_range=self._state.current_month_range,
            today_start=self._state.today_start,
        )
        return CalendarPrinter(printer_context)

    def get_time_range(self, timestamp, unit):
        start = unit.get_value("start", timestamp)
        end = start + unit.get_value("length", timestamp)
        return TimeRange(start, end)

    def print_year_calendar(self):
        year_data = self._year_calculator.calculate_year_data(self.timestamp, self.year_unit)
        self._printer.print_year_header(year_data)
        current_month = 1
        while True:
            month_data = self._month_calculator.get_month_data(
                year_data.year_start,
                current_month,
                year_data.months_across,
                self.units,
                self.timestamp,
            )
            if not month_data.month_starts:
                break
            self._printer.print_month_headers(
                year_data.year_start,
                current_month,
                year_data.months_across,
                self.year_unit.get_value("names"),
                self.month_unit,
            )

            self._printer.print_weekday_headers(
                year_data.months_across,
                month_data.month_starts,
                self.week_unit.get_value("names"),
            )

            max_weeks = self._month_calculator.calculate_max_weeks(
                month_data, self.day_unit.get_value("length", self.timestamp), self.week_length
            )
            for _ in range(max_weeks):
                self._printer.print_week_row(
                    month_data, self.day_unit.get_value("length", self.timestamp)
                )
                self._month_calculator.reset_first_day_weekdays(
                    month_data, self.day_unit.get_value("length", self.timestamp)
                )

            current_month += year_data.months_across
            print()

    def __str__(self) -> str:
        """String representation of the Calendar.

        Shows calendar name, current ranges, and available units.
        """
        unit_info = ", ".join(
            f"{unit_type}: {unit.name}"
            for unit_type, unit in self.units.items()
            if unit_type != "day_of_week_fn"
        )

        return (
            f"Calendar('{self.name}', " f"week: {self.week_length} days, " f"units: [{unit_info}])"
        )

    def __repr__(self) -> str:
        """Detailed representation of the Calendar."""
        return (
            f"Calendar(name='{self.name}', "
            f"timestamp={self.timestamp}, "
            f"week_length={self.week_length}, "
            f"today_start={self.today_start}, "
            f"week_range={self.current_week_range}, "
            f"month_range={self.current_month_range})"
        )

    @property
    def year_unit(self):
        return self.units["year"]

    @property
    def month_unit(self):
        return self.units["month"]

    @property
    def week_unit(self):
        return self.units["week"]

    @property
    def day_unit(self):
        return self.units["day"]

    @property
    def week_length(self) -> int:
        """Get week length from state."""
        return self._state.week_length

    @property
    def today_start(self) -> float:
        """Get today's start timestamp from state."""
        return self._state.today_start

    @property
    def current_week_range(self) -> TimeRange:
        """Get current week range from state."""
        return self._state.current_week_range

    @property
    def current_month_range(self) -> TimeRange:
        """Get current month range from state."""
        return self._state.current_month_range

    @property
    def day_of_week_fn(self) -> Optional[HyExpression]:
        """Get custom day-of-week function if it exists."""
        return self.units.get("day_of_week_fn")
