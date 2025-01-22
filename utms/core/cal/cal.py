from utms.utils import print_row, TimeRange, get_day_of_week, get_timezone


class Calendar:
    def __init__(self, timestamp, units):
        self.timestamp = timestamp
        self.units = units
        self.day_unit = units["day"]
        self.week_unit = units["week7"]
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
        year_start = self.year_unit.get_value("start", self.timestamp)
        year_end = year_start + self.year_unit.get_value("length", self.timestamp)
        months_across = 3

        # Calculate year number
        year_length = self.year_unit.get_value("length", self.timestamp)
        epoch_year = 1970
        years_since_epoch = int(self.timestamp / year_length)
        year_num = epoch_year + years_since_epoch
        
        # Print year header
        total_width = months_across * (self.week_length * 3 + 3)
        year_str = str(year_num)
        padding = (total_width - len(year_str)) // 2
        print(" " * padding + "\033[1;31m" + year_str + "\033[0m " * padding)
        print()
    
        # Walk through the year month by month
        current_month = 1
        current_timestamp = year_start

        while True:
            # Get month data first to check if there's anything to display
            days, month_starts, month_ends, first_day_weekdays = self.get_month_data(
                year_start, current_month, months_across
            )
            
            # If no months to display in this group, we're done
            if not month_starts:
                break
                
            # Only print headers if we have data to display
            self.print_month_headers(year_start, current_month, months_across)
            self.print_weekday_headers(months_across, month_starts)
            
            max_weeks = self.calculate_max_weeks(month_starts, month_ends, first_day_weekdays)
    
            for _ in range(max_weeks):
                self.print_week_row(days, month_starts, month_ends, first_day_weekdays)
                self.reset_first_day_weekdays(first_day_weekdays, days, month_ends, month_starts)
            
            current_month += months_across
            print()



    def print_month_headers(self, year_start, current_month, months_across):
        month_names = []
        year_unit_names = self.year_unit.get_value("names")

        current_timestamp = year_start
        valid_months_seen = 0
        month_index = 1

        # Find starting month index
        while valid_months_seen < (current_month - 1):
            month_length = self.month_unit.get_value("length", current_timestamp, month_index)
            # print(f"Skipping - index: {month_index}, length: {month_length}")
            if month_length > 0:
                valid_months_seen += 1
                current_timestamp += month_length
            month_index += 1

        # print(f"After skipping - index: {month_index}, valid_months: {valid_months_seen}")

        # Add headers only for valid months
        valid_months_added = 0
        while valid_months_added < months_across and month_index <= len(year_unit_names):
            month_length = self.month_unit.get_value("length", current_timestamp, month_index)
            # print(f"Processing - index: {month_index}, length: {month_length}")
            if month_length > 0:
                # Special handling for Year Day
                if month_index == 14:  # Year Day
                    name_index = 14  # Use actual index for Year Day
                else:
                    name_index = month_index - 1

                month_name = year_unit_names[name_index]
                # print(f"Adding month: {month_name} (index {name_index})")
                total_width = self.week_length * 3
                padding_total = total_width - len(month_name)
                padding_left = padding_total // 2
                padding_right = padding_total - padding_left
                colored_centered_month_name = (
                    " " * padding_left + f"\033[34m{month_name}\033[0m" + " " * padding_right
                )
                month_names.append(colored_centered_month_name)
                valid_months_added += 1
                current_timestamp += month_length

            month_index += 1

        print_row(month_names)


    def get_month_data(self, year_start, current_month, months_across):
        days = []
        month_starts = []
        month_ends = []
        first_day_weekdays = []

        current_timestamp = year_start
        year_end = year_start + self.year_unit.get_value("length", self.timestamp)
        max_months = len(self.year_unit.get_value("names"))

        if current_month > max_months:
            return days, month_starts, month_ends, first_day_weekdays

        # print(f"\nDebug get_month_data:")
        # print(f"Year start: {current_timestamp}")
        # print(f"Year end: {year_end}")
        # print(f"Processing months {current_month} to {current_month + months_across - 1}")

        # Skip to the start of this group
        month_index = 1
        while month_index < current_month:
            # Pass month_index to get_value
            month_length = self.month_unit.get_value("length", current_timestamp, month_index)
            # print(f"Skipping month {month_index} - ts: {current_timestamp}, length: {month_length}")
            if month_length > 0:
                current_timestamp += month_length
            month_index += 1

        # Calculate data for the current month group
        months_added = 0
        while months_added < months_across and current_timestamp < year_end and month_index <= max_months:
            # Pass month_index to get_value
            month_length = self.month_unit.get_value("length", current_timestamp, month_index)
            # print(f"Processing month {month_index} - ts: {current_timestamp}, length: {month_length}")

            if month_length > 0:
                days.append(1)
                month_starts.append(current_timestamp)
                month_end = min(current_timestamp + month_length - 1, year_end - 1)
                month_ends.append(month_end)

                first_day_weekday = (
                    get_day_of_week(current_timestamp, self.week_unit, self.day_unit)
                    % self.week_length
                )
                first_day_weekdays.append(first_day_weekday)
                months_added += 1
                current_timestamp += month_length

            month_index += 1

        return days, month_starts, month_ends, first_day_weekdays

    def calculate_max_weeks(self, month_starts, month_ends, first_day_weekdays):
        max_weeks = 0
        day_length = self.day_unit.get_value("length", self.timestamp)
        days_per_week = self.week_unit.get_value("length", self.timestamp) // day_length
        
        for i in range(len(month_starts)):
            # Calculate days in month using timestamps
            days_in_month = int((month_ends[i] - month_starts[i]) / day_length) + 1
            
            weeks_in_month = (days_in_month + first_day_weekdays[i] + (days_per_week - 1)) // days_per_week
            max_weeks = max(max_weeks, weeks_in_month)
        return max_weeks

    def print_week_row(self, days, month_starts, month_ends, first_day_weekdays):
        week_row = []
    
        for i in range(len(month_starts)):
            week_days_str = self.get_month_week_days(
                days, month_starts, month_ends, first_day_weekdays, i
            )
            total_width = (self.week_length * 2) + (self.week_length - 1)
            week_row.append(week_days_str.ljust(total_width))
        print_row(week_row)
    
    def get_month_week_days(self, days, month_starts, month_ends, first_day_weekdays, i):
        """Generates the week's days string for a specific month index."""
        month_week_days = []
        day_length = self.day_unit.get_value("length", self.timestamp)
        
        # Calculate total days in month
        days_in_month = int((month_ends[i] - month_starts[i]) / day_length) + 1
        
        for day_of_week in range(self.week_length):
            if day_of_week < first_day_weekdays[i] and days[i] == 1:
                # Pad with spaces before the first day of the month
                month_week_days.append("  ")
            elif days[i] > days_in_month:
                # No more days in this month, pad with spaces
                month_week_days.append("  ")
            else:
                # Calculate timestamp for current day
                current_day_timestamp = month_starts[i] + (days[i] - 1) * day_length
                
                is_current_month = (
                    self.current_month_range.start <= current_day_timestamp < self.current_month_range.end
                )
                day_str = self.format_day(
                    days[i],
                    is_current_month,
                    current_day_timestamp,
                )
                month_week_days.append(day_str)
                days[i] += 1
        
        # Join with single space between days
        return " ".join(month_week_days)


    def print_weekday_headers(self, months_across, month_starts=None):
        """Prints the weekday headers for a row of months."""
        weekday_names = self.week_unit.get_value("names")
        week_headers = []

        # Only print weekday headers for months that have data
        for i in range(months_across):
            if i < len(month_starts):
                week_header = " ".join(["\033[33m" + name[:2] + "\033[0m" for name in weekday_names])
                week_headers.append(week_header.ljust(self.week_length * 3))
            else:
                week_headers.append(" " * (self.week_length * 3))

        print_row(week_headers)

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
        day_length = self.day_unit.get_value("length", self.timestamp)
        
        for i in range(len(first_day_weekdays)):
            # Calculate days in month using timestamps
            days_in_month = int((month_ends[i] - month_starts[i]) / day_length) + 1
            
            if days[i] > days_in_month:
                # Month is complete, stop incrementing days[i]
                days[i] = days_in_month + 1
                first_day_weekdays[i] = 0
            else:
                first_day_weekdays[i] = 0
