import datetime

from utms.utils import TimeRange, get_day_of_week, get_timezone, print_row


class Calendar:
    def __init__(self, timestamp, units):
        self.timestamp = timestamp
        self.units = units
        self.day_unit = units["day"]
        self.week_unit = units["week7sunday"]
        self.month_unit = units["month"]
        self.year_unit = units["year"]
        self.week_length = self.week_unit.get_value("length", timestamp) // self.day_unit.get_value(
            "length", timestamp
        )
        self.today_start = self.day_unit.get_value("start", timestamp)
        self.current_week_range = self.get_time_range(timestamp, self.week_unit)
        self.current_month_range = self.get_time_range(timestamp, self.month_unit)

    def get_time_range(self, timestamp, unit):
        start = unit.get_value("start", timestamp)
        end = start + unit.get_value("length", timestamp)
        return TimeRange(start, end)

    def print_year_calendar(self):
        # Use instance variables instead of passing arguments
        timezone = get_timezone(self.year_unit, self.timestamp)
        year_start = datetime.datetime.fromtimestamp(
            self.year_unit.get_value("start", self.timestamp), tz=timezone
        )
        months_across = 3
        total_width = months_across * (self.week_length * 3 + 3)
        year_str = str(year_start.year)
        padding = (total_width - len(year_str)) // 2
        print(" " * padding + "\033[1;31m" + year_str + "\033[0m " * padding)
        print()

        current_month = 1
        total_months = len(self.year_unit.get_value("names"))

        while current_month <= total_months:
            self.print_month_headers(year_start, current_month, months_across)
            self.print_weekday_headers(months_across)
            days, month_starts, month_ends, first_day_weekdays = self.get_month_data(
                year_start, current_month, months_across
            )
            max_weeks = self.calculate_max_weeks(month_starts, month_ends, first_day_weekdays)

            for _ in range(max_weeks):
                self.print_week_row(days, month_starts, month_ends, first_day_weekdays)
                self.reset_first_day_weekdays(first_day_weekdays, days, month_ends, month_starts)
            current_month += months_across
            print()

    def print_month_headers(self, year_start, current_month, months_across):
        """Prints month headers, aligned with day grids."""
        month_names = []
        year_unit_names = self.year_unit.get_value("names")

        for i in range(months_across):
            if current_month <= len(year_unit_names):
                month_name = year_unit_names[current_month - 1]
                total_width = self.week_length * 3
                padding_total = total_width - len(month_name)
                padding_left = padding_total // 2
                padding_right = padding_total - padding_left
                colored_centered_month_name = (
                    " " * padding_left + f"\033[34m{month_name}\033[0m" + " " * padding_right
                )
                month_names.append(colored_centered_month_name)
                current_month += 1
            else:
                # Empty space for months beyond those defined
                month_names.append(" " * (self.week_length * 3))
        print_row(month_names)

    def get_month_data(self, year_start, current_month, months_across):
        """Calculates and returns month-related data for a row of months."""
        days = [1] * months_across
        month_starts = []
        month_ends = []
        first_day_weekdays = []

        for i in range(months_across):
            m = current_month + i
            if m <= len(self.year_unit.get_value("names")):
                timezone = get_timezone(self.month_unit, self.timestamp)
                # Calculate the timestamp for the start of each month individually
                month_start = datetime.datetime(year_start.year, m, 1, tzinfo=timezone)
                month_start_timestamp = month_start.timestamp()
                month_starts.append(month_start)
                # Use the correct timestamp for the month when getting its length
                month_length = self.month_unit.get_value("length", month_start_timestamp)
                month_end_timestamp = month_start_timestamp + month_length - 1
                month_end = datetime.datetime.fromtimestamp(month_end_timestamp, tz=timezone)
                month_ends.append(month_end)
                first_day_weekday = (
                    get_day_of_week(month_start_timestamp, self.week_unit, self.day_unit)
                    % self.week_length
                )
                first_day_weekdays.append(first_day_weekday)
        return days, month_starts, month_ends, first_day_weekdays

    def calculate_max_weeks(self, month_starts, month_ends, first_day_weekdays):
        max_weeks = 0
        for i in range(len(month_starts)):
            weeks_in_month = (month_ends[i].day + first_day_weekdays[i] + 6) // 7
            max_weeks = max(max_weeks, weeks_in_month)
        return max_weeks

    def print_week_row(self, days, month_starts, month_ends, first_day_weekdays):
        week_row = []

        for i in range(len(month_starts)):
            week_days_str = self.get_month_week_days(
                days, month_starts, month_ends, first_day_weekdays, i
            )
            week_row.append(week_days_str.ljust(self.week_length * 3))
        print_row(week_row)

    def get_month_week_days(self, days, month_starts, month_ends, first_day_weekdays, i):
        """Generates the week's days string for a specific month index."""
        month_week_days = []
        for day_of_week in range(self.week_length):
            if day_of_week < first_day_weekdays[i] and days[i] == 1:
                # Pad with spaces before the first day of the month
                month_week_days.append("  ")
            elif days[i] > month_ends[i].day:
                # No more days in this month, pad with spaces
                month_week_days.append("  ")
            else:
                current_date = month_starts[i].replace(day=days[i])
                current_day_timestamp = current_date.timestamp()
                is_current_month = (
                    self.current_month_range.start
                    <= current_day_timestamp
                    < self.current_month_range.end
                )
                day_str = self.format_day(
                    days[i],
                    is_current_month,
                    current_day_timestamp,
                )
                month_week_days.append(day_str)
                days[i] += 1
        return " ".join(month_week_days)

    def print_weekday_headers(self, months_across):
        """Prints the weekday headers for a row of months."""
        weekday_names = self.week_unit.get_value("names")
        week_header = " ".join(["\033[33m" + name[:2] + "\033[0m" for name in weekday_names])

        weekday_headers = [week_header.ljust(self.week_length * 3)] * months_across
        print_row(weekday_headers)

    def format_day(self, day_num, is_current_month, current_day_timestamp):
        day_str = f"{day_num:2}"
        if is_current_month:
            if self.current_week_range.start <= current_day_timestamp < self.current_week_range.end:
                if self.day_unit.get_value("start", current_day_timestamp) == self.today_start:
                    # Highlight current day in red background
                    day_str = f"\033[41m{day_str}\033[0m"
                else:
                    # Highlight other days in current week in cyan
                    day_str = f"\033[96m{day_str}\033[0m"
            else:
                # Highlight days in current month but not in current week in green
                day_str = f"\033[32m{day_str}\033[0m"
        return day_str

    def reset_first_day_weekdays(self, first_day_weekdays, days, month_ends, month_starts):
        """Resets first_day_weekdays after the first week."""
        for i in range(len(first_day_weekdays)):
            if days[i] > month_ends[i].day:
                # Month is complete, stop incrementing days[i]
                days[i] = month_ends[i].day + 1
                first_day_weekdays[i] = 0
            else:
                first_day_weekdays[i] = 0
