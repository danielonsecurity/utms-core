import time
import datetime
from types import FunctionType
from utms.utms_types import CalendarUnit, HyExpression
from typing import Dict, Optional
from utms.utils import get_timezone_from_seconds, get_datetime_from_timestamp, get_day_of_week
from utms.resolvers import evaluate_hy_expression

from .calendar_data import MonthData, YearData

class YearCalculator:
    """Handles year-related calculations."""
    epoch_year: int = 1970

    def calculate_year_data(self, timestamp: float, year_unit: CalendarUnit) -> YearData:
        """Calculate year-related data from timestamp."""
        year_start = year_unit.get_value("start", timestamp)
        year_length = year_unit.get_value("length", timestamp)
        years_since_epoch = int(timestamp / year_length)
        year_num = self.epoch_year + years_since_epoch
        
        return YearData(
            year_num=year_num,
            year_start=year_start,
            year_length=year_length
        )

class DayOfWeekCalculator:
    """Handles day of week calculations with support for custom functions."""
    
    def __init__(self):
        self._func_cache = {}

    def calculate(
        self,
        timestamp: float,
        units: Dict[str, CalendarUnit],
        custom_fn: Optional[HyExpression] = None
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


class MonthCalculator:
    """Handles month-related calculations."""
    def __init__(self):
        self._day_of_week_calculator = DayOfWeekCalculator()

    def get_month_data(
        self, 
        year_start: float,
        current_month: int,
        months_across: int,
        units: Dict[str, CalendarUnit],
        timestamp: float,
    ) -> MonthData:
        """Calculate month data for calendar display."""
        year_unit = units["year"]
        month_unit = units["month"]
        week_unit = units["week"]
        day_unit = units["day"]
        custom_day_of_week = units["day_of_week_fn"]
        if current_month > len(year_unit.get_value("names")):
            return MonthData([], [], [], [])

        days = []
        month_starts = []
        month_ends = []
        first_day_weekdays = []

        current_timestamp = year_start
        year_end = year_start + year_unit.get_value("length", timestamp)
        max_months = len(year_unit.get_value("names"))
        week_length = week_unit.get_value("length", timestamp) // day_unit.get_value("length", timestamp)
        # Skip to the start of this group
        month_index = 1
        while month_index < current_month:
            month_length = month_unit.get_value("length", current_timestamp, month_index)
            if month_length > 0:
                current_timestamp += month_length
            month_index += 1

        # Calculate data for the current month group
        months_added = 0
        while (months_added < months_across 
               and current_timestamp < year_end 
               and month_index <= max_months):
            
            month_length = month_unit.get_value("length", current_timestamp, month_index)

            if month_length > 0:
                days.append(1)
                month_starts.append(current_timestamp)
                month_end = min(current_timestamp + month_length - 1, year_end - 1)
                month_ends.append(month_end)

                first_day_weekday = self._day_of_week_calculator.calculate(
                    current_timestamp, units, custom_day_of_week
                ) % week_length
                first_day_weekdays.append(first_day_weekday)
                months_added += 1
                current_timestamp += month_length

            month_index += 1

        return MonthData(days, month_starts, month_ends, first_day_weekdays)

    def calculate_max_weeks(
        self,
        month_data: MonthData,
        day_length: float,
        days_per_week: int,
    ) -> int:
        """Calculate maximum weeks needed to display the months."""
        max_weeks = 0

        for i in range(len(month_data.month_starts)):
            days_in_month = int(
                (month_data.month_ends[i] - month_data.month_starts[i]) / day_length
            ) + 1

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
            days_in_month = int(
                (month_data.month_ends[i] - month_data.month_starts[i]) / day_length
            ) + 1

            if month_data.days[i] > days_in_month:
                month_data.days[i] = days_in_month + 1
                month_data.first_day_weekdays[i] = 0
            else:
                month_data.first_day_weekdays[i] = 0
