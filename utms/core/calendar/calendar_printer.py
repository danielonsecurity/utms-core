# utms/core/calendar/printer.py
from dataclasses import dataclass
from typing import Dict

from utms.utms_types import CalendarUnit, NamesList, TimeRange

from .calendar_data import MonthData, Timestamp, YearData
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


@dataclass
class PrinterContext:
    """Context for printer operations."""

    week_length: int
    current_week_range: TimeRange
    current_month_range: TimeRange
    today_start: Timestamp


class CalendarPrinter:
    """Handles all calendar display operations."""

    def __init__(self, context: PrinterContext):
        self._context = context
        self._year_formatter = YearHeaderFormatter()
        self._month_formatter = MonthHeaderFormatter(context.week_length)
        self._weekday_formatter = WeekdayHeaderFormatter(context.week_length)
        self._day_formatter = DayFormatter()
        self._week_row_formatter = WeekRowFormatter(context.week_length, self._day_formatter)

    def print_year_header(self, year_data: YearData) -> None:
        """Print the year header."""
        header = self._year_formatter.format_year_header(
            YearContext(
                timestamp=year_data.year_start,
                year_length=year_data.year_length,
                months_across=year_data.months_across,
                week_length=self._context.week_length,
            )
        )
        print(header)
        print()

    def print_month_headers(
        self,
        year_start: Timestamp,
        current_month: int,
        months_across: int,
        year_unit_names: NamesList,
        month_unit: CalendarUnit,
    ) -> None:
        """Print headers for the current row of months."""
        month_names = []
        month_index = 1
        valid_months_seen = 0
        current_timestamp = year_start

        # Find starting month index
        while valid_months_seen < (current_month - 1):
            month_length = month_unit.get_value("length", current_timestamp, month_index)
            if month_length > 0:
                valid_months_seen += 1
                current_timestamp += month_length
            month_index += 1

        # Add headers for valid months
        valid_months_added = 0
        while valid_months_added < months_across and month_index <= len(year_unit_names):
            month_length = month_unit.get_value("length", current_timestamp, month_index)
            if month_length > 0:
                name_index = 14 if month_index == 14 else month_index - 1
                month_names.append(year_unit_names[name_index])
                valid_months_added += 1
                current_timestamp += month_length
            month_index += 1

        formatted_headers = self._month_formatter.format_month_headers(month_names, months_across)
        print(formatted_headers)

    def print_weekday_headers(
        self,
        months_across: int,
        month_starts: list[float],
        weekday_names: list[str],
    ) -> None:
        """Print weekday headers for all visible months."""
        formatted_headers = self._weekday_formatter.format_weekday_row(
            weekday_names, months_across, month_starts
        )
        print(formatted_headers)

    def print_week_row(self, month_data: MonthData, day_length: float) -> None:
        """Print a week row across all months."""
        day_context = DayContext(
            current_week_range=self._context.current_week_range,
            today_start=self._context.today_start,
            day_start=0,
        )
        week_context = WeekContext(
            week_length=self._context.week_length,
            days=month_data.days,
            month_starts=month_data.month_starts,
            month_ends=month_data.month_ends,
            first_day_weekdays=month_data.first_day_weekdays,
            day_length=day_length,
        )

        formatted_row = self._week_row_formatter.format_week_row(
            week_context, day_context, self._context.current_month_range
        )
        print(formatted_row)
