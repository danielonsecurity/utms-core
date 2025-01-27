import datetime
import time
from decimal import Decimal
from types import FunctionType

from utms.resolvers import evaluate_hy_expression
from utms.utils import (
    get_datetime_from_timestamp,
    get_day_of_week,
    get_logger,
    get_timezone_from_seconds,
)
from utms.utms_types import (
    CalendarUnit,
    FunctionCache,
    OptionalHyExpression,
    TimeLength,
    TimeRange,
    TimeStamp,
)

from .calendar_data import MonthCalculationParams, MonthContext, MonthData, MonthGroupData, YearData
from .unit_accessor import UnitAccessor

logger = get_logger("core.calendar.calendar_calculator")


class DayOfWeekCalculator:  # pylint: disable=too-few-public-methods
    """Handles day of week calculations with support for custom functions."""

    def __init__(self) -> None:
        self._func_cache: FunctionCache = {}

    def calculate(
        self,
        timestamp: TimeStamp,
        units: UnitAccessor,
        custom_fn: OptionalHyExpression = None,
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
            result = func(timestamp)
            # Handle each possible type
            if isinstance(result, int):
                return result
            if isinstance(result, (float, Decimal)):
                return int(result)
            if isinstance(result, str):
                return int(float(result))
            raise TypeError(f"Cannot convert result to int: {result} (type: {type(result)})")
        return get_day_of_week(timestamp, units["week"], units["day"])


class CalendarCalculator:
    def __init__(self) -> None:
        self._day_of_week_calculator = DayOfWeekCalculator()
        self.epoch_year: int = 1970

    def calculate_time_range(self, timestamp: TimeStamp, unit: CalendarUnit) -> TimeRange:
        start = unit.get_start(timestamp)
        end = start + unit.get_length(timestamp)
        return TimeRange(start, end)

    def calculate_year_data(self, timestamp: TimeStamp, year_unit: CalendarUnit) -> YearData:
        """Calculate year-related data."""
        year_start = year_unit.get_start(timestamp)
        year_length = year_unit.get_length(timestamp)
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
        names = year_unit.get_names()
        if names is None:
            raise ValueError("Year names list cannot be None")
        return current_month <= len(names)

    def _calculate_week_length(self, units: UnitAccessor, timestamp: TimeStamp) -> int:
        """Calculate week length in days."""
        return units.week.get_length(timestamp) // units.day.get_length(timestamp)

    def _create_month_context(self, params: MonthCalculationParams) -> MonthContext:
        """Create context for month calculations."""
        year_end = params.year_start.copy() + params.units.year.get_length(params.timestamp)
        names = params.units.year.get_names()
        if names is None:
            raise ValueError("Year names list cannot be None")
        max_months = len(names)

        # Skip to start of current month group
        current_timestamp = self._skip_to_month_group(
            params.year_start.copy(), params.current_month, params.units.month
        )

        return MonthContext(
            current_timestamp=current_timestamp.copy(),
            year_end=year_end.copy(),
            max_months=max_months,
            month_index=params.current_month,
            months_across=params.months_across,
        )

    def _skip_to_month_group(
        self,
        year_start: TimeStamp,
        current_month: int,
        month_unit: CalendarUnit,
    ) -> TimeStamp:
        """Skip to the start of the current month group."""
        current_timestamp = year_start.copy()
        month_index = 1

        while month_index < current_month:
            month_length = month_unit.get_length(current_timestamp, month_index=month_index)
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
        logger.debug(
            "Processing month %d:\nCurrent timestamp: %s",
            context.month_index,
            context.current_timestamp,
        )

        month_length = units.month.get_length(
            context.current_timestamp, month_index=context.month_index
        )
        logger.debug("Month length: %d days", month_length // 86400)

        if month_length > 0:
            current_ts = context.current_timestamp.copy()
            month_end = min((current_ts + month_length - 1).copy(), (context.year_end - 1).copy())
            logger.debug("Month end: %s\nCurrent TS: %s", month_end, current_ts)
            first_day_weekday = (
                self._day_of_week_calculator.calculate(
                    context.current_timestamp.copy(), units, units.day_of_week_fn
                )
                % week_length
            )
            logger.debug("First day weekday: %d", first_day_weekday)

            group_data.add_month(
                context.current_timestamp.copy(), month_end.copy(), first_day_weekday
            )
            context.months_added += 1
            context.current_timestamp += month_length
            logger.debug("New current timestamp: %s", context.current_timestamp)

    def calculate_max_weeks(
        self,
        month_data: MonthData,
        day_length: TimeLength,
        days_per_week: int,
    ) -> int:
        """Calculate maximum weeks needed to display the months."""
        max_weeks = 0

        for month in zip(
            month_data.month_starts, month_data.month_ends, month_data.first_day_weekdays
        ):
            month_start, month_end, first_day_weekday = month
            logger.debug(
                "Calculating weeks for month:\n  start: %s\n  end: %s\n  first_day_weekday: %d",
                month_start,
                month_end,
                first_day_weekday,
            )

            month_duration = month_end - month_start
            days_in_month = int(month_duration / day_length) + 1
            logger.debug("  days_in_month: %d", days_in_month)

            total_slots_needed = days_in_month + first_day_weekday
            weeks_in_month = (total_slots_needed + days_per_week - 1) // days_per_week
            logger.debug("  weeks_in_month: %d", weeks_in_month)

            max_weeks = max(max_weeks, weeks_in_month)
            logger.debug("  max_weeks: %d", max_weeks)

        return int(max_weeks)

    def reset_first_day_weekdays(
        self,
        month_data: MonthData,
        day_length: TimeLength,
    ) -> None:
        """Reset first day weekdays after processing a week."""
        for month_idx, (month_end, month_start) in enumerate(
            zip(month_data.month_ends, month_data.month_starts)
        ):
            days_in_month = int((month_end - month_start) / day_length) + 1

            if month_data.days[month_idx] > days_in_month:
                month_data.days[month_idx] = days_in_month + 1
                month_data.first_day_weekdays[month_idx] = 0
            else:
                month_data.first_day_weekdays[month_idx] = 0
