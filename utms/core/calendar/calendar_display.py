from dataclasses import dataclass

from utms.utils import ColorFormatter, TimeRange
from utms.utms_types import (
    IntegerList,
    NamesList,
    OptionalInteger,
    OptionalTimeStampList,
    TimeLength,
    TimeStamp,
    TimeStampList,
)

from .calendar_data import YearContext


class MonthHeaderFormatter:
    """Handles formatting of month headers in calendar display."""

    def __init__(self, week_length: int):
        self.week_length = week_length

    def format_month_header(self, month_name: str, total_width: OptionalInteger = None) -> str:
        """Format a month name as a centered header.

        Args:
            month_name: Name of the month
            total_width: Optional total width for centering

        Returns:
            Formatted month header string
        """
        width = total_width or self.week_length * 3
        padding_total = width - len(month_name)
        padding_left = int(padding_total // 2)
        padding_right = int(padding_total - padding_left)

        return " " * padding_left + ColorFormatter.blue(month_name) + " " * padding_right

    def format_month_headers(self, month_names: NamesList, months_across: int) -> str:
        """Format multiple month headers for display.

        Args:
            month_names: List of month names
            months_across: Number of months to display across

        Returns:
            List of formatted month header strings
        """
        headers = []
        total_width = self.week_length * 3

        if month_names:
            for month_name in month_names[:months_across]:
                headers.append(self.format_month_header(month_name, total_width))

        return "  ".join(headers)


class WeekdayHeaderFormatter:
    """Handles formatting of weekday headers in calendar display."""

    def __init__(self, week_length: int):
        self.week_length = week_length

    def format_weekday_name(self, name: str) -> str:
        """Format a single weekday name."""
        return ColorFormatter.yellow(name[:2])

    def format_weekday_row(
        self,
        weekday_names: NamesList,
        months_across: int,
        month_starts: OptionalTimeStampList = None,
    ) -> str:
        """Format weekday headers for all visible months."""
        week_headers = []

        for i in range(months_across):
            if weekday_names and month_starts and i < len(month_starts):
                # Format weekday names for this month
                formatted_names = [self.format_weekday_name(name) for name in weekday_names]
                week_header = " ".join(formatted_names)
                week_headers.append(week_header.ljust(int(self.week_length) * 3))
            else:
                # Empty space for months without data
                week_headers.append(" " * (self.week_length * 3))

        return "  ".join(week_headers)


@dataclass
class DayContext:
    """Context for day formatting decisions."""

    current_week_range: TimeRange
    today_start: TimeStamp
    day_start: TimeStamp


class DayFormatter:  # pylint: disable=too-few-public-methods
    """Handles formatting of day numbers in calendar display."""

    def format_day(
        self,
        day_num: int,
        is_current_month: bool,
        current_day_timestamp: TimeStamp,
        context: DayContext,
    ) -> str:
        day_str = f"{day_num:2}"

        if not is_current_month:
            return day_str

        # Check if day is in current week
        in_current_week = (
            context.current_week_range.start
            <= current_day_timestamp
            < context.current_week_range.end
        )

        if in_current_week:
            # Check if this is today
            is_today = current_day_timestamp == context.today_start
            if is_today:
                return ColorFormatter.red_bg(day_str)
            return ColorFormatter.cyan(day_str)
        return ColorFormatter.green(day_str)


@dataclass
class WeekContext:
    """Context for week row formatting."""

    week_length: int
    days: IntegerList
    month_starts: TimeStampList
    month_ends: TimeStampList
    first_day_weekdays: IntegerList
    day_length: TimeLength


class WeekRowFormatter:
    """Handles formatting of week rows in calendar display."""

    def __init__(self, week_length: int, day_formatter: DayFormatter):
        self.week_length = week_length
        self.day_formatter = day_formatter

    def format_month_week_days(
        self,
        context: WeekContext,
        month_idx: int,
        day_context: DayContext,
        is_current_month: bool,
    ) -> str:
        """Format a week's days for a specific month."""
        month_week_days = []

        # Calculate total days in month
        days_in_month = (
            int(
                (context.month_ends[month_idx] - context.month_starts[month_idx])
                / context.day_length
            )
            + 1
        )

        for day_of_week in range(self.week_length):
            # Before first day of month
            if day_of_week < context.first_day_weekdays[month_idx] and context.days[month_idx] == 1:
                month_week_days.append("  ")

            # After last day of month
            elif context.days[month_idx] > days_in_month:
                month_week_days.append("  ")

            # Regular day
            else:
                current_day_timestamp = (
                    context.month_starts[month_idx]
                    + (context.days[month_idx] - 1) * context.day_length
                )

                day_str = self.day_formatter.format_day(
                    context.days[month_idx], is_current_month, current_day_timestamp, day_context
                )
                month_week_days.append(day_str)
                context.days[month_idx] += 1

        return " ".join(month_week_days)

    def format_week_row(
        self, context: WeekContext, day_context: DayContext, current_month_range: TimeRange
    ) -> str:
        """Format a complete week row across all months."""
        week_row = []
        total_width = (self.week_length * 2) + (self.week_length - 1)

        for month_idx, month_start in enumerate(context.month_starts):
            # for i in range(len(context.month_starts)):
            # Check if this month is the current month
            is_current_month = current_month_range.start <= month_start < current_month_range.end
            week_days_str = self.format_month_week_days(
                context, month_idx, day_context, is_current_month
            )
            week_row.append(week_days_str.ljust(total_width))

        return "  ".join(week_row)


class YearHeaderFormatter:
    """Handles formatting of year headers in calendar display."""

    def calculate_year_number(self, context: YearContext) -> int:
        """Calculate the year number from timestamp."""
        years_since_epoch = int(context.timestamp / context.year_length)
        return context.epoch_year + years_since_epoch

    def format_year_header(self, context: YearContext) -> str:
        """Format the year header with proper centering and color."""
        year_num = self.calculate_year_number(context)
        total_width = context.months_across * (context.week_length * 3 + 3)

        year_str = str(year_num)
        padding = int((total_width - len(year_str)) // 2)

        return " " * padding + ColorFormatter.red(year_str) + " " * padding
