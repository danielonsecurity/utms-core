import datetime
import time
from dataclasses import dataclass
from types import FunctionType
from typing import Dict, List, Optional

from utms.resolvers import evaluate_hy_expression
from utms.utils import get_datetime_from_timestamp, get_day_of_week, get_timezone_from_seconds
from utms.utms_types import CalendarUnit, HyExpression, TimeRange, Timestamp

from .calendar_data import MonthCalculationParams, MonthContext, MonthData, MonthGroupData, YearData
from .unit_accessor import UnitAccessor


class DayOfWeekCalculator:  # pylint: disable=too-few-public-methods
    """Handles day of week calculations with support for custom functions."""

    def __init__(self):
        self._func_cache = {}

    def calculate(
        self,
        timestamp: Timestamp,
        units: Dict[str, CalendarUnit],
        custom_fn: Optional[HyExpression] = None,
    ) -> int:
        """Calculate day of week for timestamp."""
        if custom_fn:
            if "day_of_week" in self._func_cache:
                func = self._func_cache["day_of_week"]
            else:
                base_func = evaluate_hy_expression(custom_fn, {})
                func_globals = {
                    **base_func.__globals__,
                    "datetime": datetime,
                    "time": time,
                    "get_day_of_week": get_day_of_week,
                    "get_timezone": get_timezone_from_seconds,
                    "get_datetime_from_timestamp": get_datetime_from_timestamp,
                    **units,
                }
                func = FunctionType(
                    base_func.__code__,
                    func_globals,
                    base_func.__name__,
                    base_func.__defaults__,
                    base_func.__closure__,
                )
                self._func_cache["day_of_week"] = func
            return func(timestamp)
        else:
            return get_day_of_week(timestamp, units["week"], units["day"])


class CalendarCalculator:
    def __init__(self) -> None:
        self._day_of_week_calculator = DayOfWeekCalculator()
        self.epoch_year: int = 1970

    def calculate_time_range(self, timestamp: Timestamp, unit: CalendarUnit) -> TimeRange:
        start = unit.get_value("start", timestamp)
        end = start + unit.get_value("length", timestamp)
        return TimeRange(start, end)

    def calculate_year_data(self, timestamp: Timestamp, year_unit: CalendarUnit) -> YearData:
        """Calculate year-related data."""
        year_start = year_unit.get_value("start", timestamp)
        year_length = year_unit.get_value("length", timestamp)
        years_since_epoch = int(timestamp / year_length)
        year_num = self.epoch_year + years_since_epoch

        return YearData(year_num=year_num, year_start=year_start, year_length=year_length)

    def calculate_month_data(
        self,
        params: MonthCalculationParams,
    ) -> MonthData:
        """Calculate month data for calendar display."""
        if not self._is_valid_month(params.current_month, params.units.year):
            return MonthData([], [], [], [])

        week_length = self._calculate_week_length(params.units, params.timestamp)
        month_context = self._create_month_context(params)

        return self._collect_month_data(month_context, params.units, week_length)

    def _is_valid_month(self, current_month: int, year_unit: CalendarUnit) -> bool:
        """Check if month number is valid."""
        return current_month <= len(year_unit.get_value("names"))

    def _calculate_week_length(self, units: UnitAccessor, timestamp: Timestamp) -> int:
        """Calculate week length in days."""
        return units.week.get_value("length", timestamp) // units.day.get_value("length", timestamp)

    def _create_month_context(self, params) -> MonthContext:
        """Create context for month calculations."""
        year_end = params.year_start + params.units.year.get_value("length", params.timestamp)
        max_months = len(params.units.year.get_value("names"))

        # Skip to start of current month group
        current_timestamp = self._skip_to_month_group(
            params.year_start, params.current_month, params.units.month
        )

        return MonthContext(
            current_timestamp=current_timestamp,
            year_end=year_end,
            max_months=max_months,
            month_index=params.current_month,
            months_across=params.months_across,
        )

    def _skip_to_month_group(
        self,
        year_start: Timestamp,
        current_month: int,
        month_unit: CalendarUnit,
    ) -> Timestamp:
        """Skip to the start of the current month group."""
        current_timestamp = year_start
        month_index = 1

        while month_index < current_month:
            month_length = month_unit.get_value("length", current_timestamp, month_index)
            if month_length > 0:
                current_timestamp += month_length
            month_index += 1

        return current_timestamp

    def _collect_month_data(
        self,
        context: MonthContext,
        units: UnitAccessor,
        week_length: int,
    ) -> MonthData:
        """Collect data for all months in the group."""
        group_data = MonthGroupData.empty()

        while (
            context.months_added < context.months_across
            and context.current_timestamp < context.year_end
            and context.month_index <= context.max_months
        ):
            self._process_month(context, units, week_length, group_data)
            context.month_index += 1

        return group_data.to_month_data()

    def _process_month(
        self,
        context: MonthContext,
        units: UnitAccessor,
        week_length: int,
        group_data: MonthGroupData,
    ) -> None:
        month_length = units.month.get_value(
            "length", context.current_timestamp, context.month_index
        )

        if month_length > 0:
            month_end = min(context.current_timestamp + month_length - 1, context.year_end - 1)
            first_day_weekday = (
                self._day_of_week_calculator.calculate(
                    context.current_timestamp, units, units.day_of_week_fn
                )
                % week_length
            )
            group_data.add_month(context.current_timestamp, month_end, first_day_weekday)
            context.months_added += 1
            context.current_timestamp += month_length

    def calculate_max_weeks(
        self,
        month_data: MonthData,
        day_length: float,
        days_per_week: int,
    ) -> int:
        """Calculate maximum weeks needed to display the months."""
        max_weeks = 0

        for i in range(len(month_data.month_starts)):
            days_in_month = (
                int((month_data.month_ends[i] - month_data.month_starts[i]) / day_length) + 1
            )

            weeks_in_month = (
                days_in_month + month_data.first_day_weekdays[i] + (days_per_week - 1)
            ) // days_per_week
            max_weeks = max(max_weeks, weeks_in_month)

        return max_weeks

    def reset_first_day_weekdays(
        self,
        month_data: MonthData,
        day_length: float,
    ) -> None:
        """Reset first day weekdays after processing a week."""
        for i in range(len(month_data.first_day_weekdays)):
            days_in_month = (
                int((month_data.month_ends[i] - month_data.month_starts[i]) / day_length) + 1
            )

            if month_data.days[i] > days_in_month:
                month_data.days[i] = days_in_month + 1
                month_data.first_day_weekdays[i] = 0
            else:
                month_data.first_day_weekdays[i] = 0
