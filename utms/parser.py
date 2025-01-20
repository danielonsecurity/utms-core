import datetime
import time
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from types import FunctionType

import uuid
import hy
from hy.compiler import hy_eval
from hy.models import Expression, Integer, Lazy, List, String, Symbol


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
        self._func_cache = {}  # Add a cache for functions

    def get_value(self, prop, timestamp=0):
        value = getattr(self, prop)
        if callable(value):
            # Check if the function with updated globals is cached
            if prop in self._func_cache:
                func_with_globals = self._func_cache[prop]
            else:
                func = value
                # Copy the function's globals and inject 'self' and other units
                func_globals = func.__globals__.copy()
                func_globals["self"] = self

                # Include other units if they are referenced
                func_globals.update(self.units)

                # Create a new function with the updated globals
                func_with_globals = FunctionType(func.__code__, func_globals)

                # Cache the function for future use
                self._func_cache[prop] = func_with_globals

            return func_with_globals(timestamp)

        elif isinstance(value, (int, float, str, Decimal, list)):
            # Directly return built-in types
            return value

        else:
            # Resolve Hy expressions or symbols
            resolved_value = resolve_unit_property(value, self.units, self, timestamp)
            return resolved_value


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
        print_row(month_names, width=self.week_length * 3)


    def get_month_data(self, year_start, current_month, months_across):
        """Calculates and returns month-related data for a row of months."""
        days = [1] * months_across
        month_starts = []
        month_ends = []
        first_day_weekdays = []
    
        for i in range(months_across):
            m = current_month + i
            if m <= len(self.year_unit.get_value('names')):
                timezone = get_timezone(self.month_unit, self.timestamp)
                # Calculate the timestamp for the start of each month individually
                month_start = datetime.datetime(year_start.year, m, 1, tzinfo=timezone)
                month_start_timestamp = month_start.timestamp()
                month_starts.append(month_start)
                # Use the correct timestamp for the month when getting its length
                month_length = self.month_unit.get_value('length', month_start_timestamp)
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
        print_row(week_row, width=self.week_length * 3)

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
                    self.current_month_range.start <= current_day_timestamp < self.current_month_range.end
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
        print_row(weekday_headers, width=self.week_length * 3)

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


def get_timezone(unit, timestamp=None):
    timezone_offset_seconds = unit.get_value("timezone", timestamp)

    return datetime.timezone(datetime.timedelta(seconds=float(timezone_offset_seconds)))


def get_day_of_week(timestamp: float, week_unit: CalendarUnit, day_unit: CalendarUnit) -> int:
    timezone = get_timezone(day_unit, timestamp)
    reference_datetime = datetime.datetime(1970, 1, 1, tzinfo=timezone) + datetime.timedelta(
        days=week_unit.offset
    )
    reference_timestamp = reference_datetime.timestamp()

    total_days_elapsed = (timestamp - reference_timestamp) // day_unit.get_value(
        "length", timestamp
    )
    day_of_week = int(
        total_days_elapsed
        % (week_unit.get_value("length", timestamp) // day_unit.get_value("length", timestamp))
    )

    return day_of_week


def evaluate_hy_file(hy_file_path):
    """Evaluates the HyLang file and returns the resulting data structures."""
    with open(hy_file_path, "r") as file:
        hy_code = file.read()
    return hy.read_many(hy_code)


def _resolve_symbol(expr, units, current_unit, timestamp, local_names=None, resolving=None):
    sym_str = str(expr)
    resolving = resolving or set()

    if sym_str in local_names:
        return local_names[sym_str]

    if current_unit and hasattr(current_unit, sym_str):
        return current_unit.get_value(sym_str, timestamp)

    if "." in sym_str:
        unit_name, prop_name = sym_str.split(".", 1)

        if unit_name in resolving:
            raise ValueError(f"Circular dependency detected: {unit_name}.{prop_name}")

        resolving.add(unit_name)

        if unit_name not in units:
            units[unit_name] = CalendarUnit(unit_name, units=units)

        try:
            resolved_prop = getattr(units[unit_name], prop_name)
            if isinstance(resolved_prop, (Expression, Symbol)):
                resolved_prop = resolve_unit_property(
                    resolved_prop, units, units[unit_name], timestamp, local_names, resolving
                )
            return resolved_prop
        except AttributeError:
            return None  # Or handle undefined attributes as needed
        finally:
            resolving.remove(unit_name)
    else:
        # Handle symbols that are not qualified with a unit name
        if sym_str in units:
            return units[sym_str]
        else:
            return None  # Or handle undefined symbols as needed


def _resolve_list(expr, units, current_unit, timestamp, local_names=None, resolving=None):
    return [
        (
            resolve_unit_property(item, units, current_unit, timestamp, local_names, resolving)
            if isinstance(item, (Expression, Symbol, List))
            else item
        )  # Only resolve if it's a Hy expression
        for item in expr
    ]


def _resolve_expression(expr, units, current_unit, timestamp, local_names=None, resolving=None):
    resolved_subexprs = []

    if local_names is None:
        local_names = {}

    for subexpr in expr:
        if isinstance(subexpr, Expression):
            resolved = resolve_unit_property(
                subexpr, units, current_unit, timestamp, local_names, resolving
            )
            if callable(resolved):
                resolved_subexprs.append(subexpr)
            else:
                resolved_subexprs.append(resolved)
        else:
            resolved_subexprs.append(subexpr)

    locals_dict = {
        "__builtins__": globals()["__builtins__"],
        "time": time,
        "datetime": datetime,
        "get_day_of_week": get_day_of_week,
        **units,
    }

    if current_unit:
        locals_dict["self"] = current_unit

    for i, item in enumerate(resolved_subexprs):
        if isinstance(item, Expression) and isinstance(item[0], Symbol) and str(item[0]) == "fn":
            func_name = f"_utms_{uuid.uuid4().hex}"
            locals_dict[func_name] = hy_eval(item, locals_dict)
            resolved_subexprs[i] = Symbol(func_name)
            local_names[func_name] = locals_dict[func_name]

    # Update locals_dict with local_names unconditionally
    locals_dict.update(local_names)

    try:
        value = hy_eval(Expression(resolved_subexprs), locals_dict)
    except NameError as e:
        # Return the unresolved expression to be handled later
        return Expression(resolved_subexprs)
    except Exception as e:
        # Re-raise other exceptions
        raise e

    return value


def resolve_unit_property(
    expr, units, current_unit=None, timestamp=None, local_names=None, resolving=None
):
    """Recursively resolves unit properties."""

    if isinstance(expr, (Integer, float, int, Decimal, complex)):
        return expr  # Return numeric types as is

    elif isinstance(expr, String):
        return str(expr)  # Return string values

    elif isinstance(expr, Symbol):
        return _resolve_symbol(expr, units, current_unit, timestamp, local_names, resolving)

    elif isinstance(expr, List):
        return _resolve_list(expr, units, current_unit, timestamp, local_names, resolving)

    elif isinstance(expr, Expression):
        return _resolve_expression(expr, units, current_unit, timestamp, local_names, resolving)

    else:
        return expr  # Return other types as is


def parse_unit_definitions(units_data):
    units = {}
    for unit_def_expr in units_data:
        if not isinstance(unit_def_expr, Expression) or unit_def_expr[0] != Symbol("defunit"):
            raise ValueError("Invalid unit definition format.")

        # Extract unit name and properties
        _, unit_name_sym, *unit_properties = unit_def_expr
        unit_name = str(unit_name_sym)
        unit_kwargs = {}

        for prop_expr in unit_properties:
            if isinstance(prop_expr, Expression):
                prop_name = str(prop_expr[0])
                prop_value = prop_expr[1]
                unit_kwargs[prop_name] = prop_value
            else:
                raise ValueError(f"Unexpected item type in unit properties: {type(prop_expr)}")

        units[unit_name] = {"name": unit_name, "kwargs": unit_kwargs}

    return units


def initialize_units(parsed_units, timestamp):
    units = {}
    # First, create all CalendarUnit instances
    for unit_name, unit_info in parsed_units.items():
        unit_kwargs = unit_info["kwargs"]
        units[unit_name] = CalendarUnit(name=unit_name, units=units, **unit_kwargs)
    return units


def resolve_unit_properties(units, timestamp):
    for unit in units.values():
        for prop_name, prop_value in unit.__dict__.items():
            if prop_name != "name" and isinstance(prop_value, (Expression, Symbol, List)):
                resolved_value = resolve_unit_property(prop_value, units, unit, timestamp)
                setattr(unit, prop_name, resolved_value)


def calculate_unit_indexes(units, timestamp):
    for unit in units.values():
        index = unit.get_value("index", timestamp)
        names = unit.get_value("names")
        length = unit.get_value("length", timestamp)
        start = unit.get_value("start", timestamp)

        if not index and names and length and start:
            names_len = len(names)
            unit_length = length
            unit_start = start
            # Proceed only if unit_length is non-zero
            if unit_length:
                unit.index = int((timestamp - unit_start) / unit_length * names_len)
            else:
                unit.index = 0


def process_units(units_data, timestamp):
    parsed_units = parse_unit_definitions(units_data)
    units = initialize_units(parsed_units, timestamp)
    resolve_unit_properties(units, timestamp)
    calculate_unit_indexes(units, timestamp)
    return units


def print_month_calendar(timestamp, year_unit, month_unit, week_unit, day_unit):
    """Prints the calendar, highlighting the current week and day with colors."""
    timezone = get_timezone(month_unit)
    month_start = datetime.datetime.fromtimestamp(
        month_unit.get_value("start", timestamp), tz=timezone
    )
    month_end_timestamp = month_unit.get_value("start", timestamp) + month_unit.get_value(
        "length", timestamp
    )
    week_start_datetime = datetime.datetime.fromtimestamp(
        week_unit.get_value("start", timestamp), tz=timezone
    )
    current_week_start = week_start_datetime.timestamp()
    current_week_end = current_week_start + week_unit.get_value("length", timestamp)
    month_name = year_unit.get_value("names")[year_unit.get_value("index", timestamp)]
    total_width = (
        week_unit.get_value("length", timestamp) // day_unit.get_value("length", timestamp)
    ) * 3
    padding = (total_width - len(month_name)) // 2

    print(" " * padding + f"\033[34m{month_name}\033[0m")
    print(" ".join(["\033[33m" + name[:2] + "\033[0m" for name in week_unit.names]))
    week_day_length = week_unit.get_value("length", timestamp) // day_unit.get_value(
        "length", timestamp
    )
    current_day = month_start.replace(day=1)
    first_day_weekday = (
        get_day_of_week(current_day.timestamp(), week_unit, day_unit) % week_day_length
    )
    print("   " * first_day_weekday, end="")
    day_num = 1
    while current_day.timestamp() < month_end_timestamp:
        if current_week_start <= current_day.timestamp() < current_week_end:
            if current_day.timestamp() == (day_unit.get_value("start", timestamp)):  # today
                print(f"\033[41m{day_num:2}\033[0m ", end="")
            else:
                print(f"\033[96m{day_num:2}\033[0m ", end="")
        else:
            print(f"\033[32m{day_num:2}\033[0m ", end="")
        if (
            get_day_of_week(current_day.timestamp(), week_unit, day_unit)
        ) % week_day_length == week_day_length - 1:
            print()
        current_day += datetime.timedelta(days=1)
        day_num += 1
    print()






def print_row(items_list, width, separator="   "):
    """Prints a row of items with formatting."""
    formatted_items = []
    for items in items_list:
        formatted_items.append(f"{items}")
    print(separator.join(formatted_items))


def print_month_headers(year_start, current_month, months_across, week_length, year_unit):
    """Prints month headers, aligned with day grids."""
    month_names = []
    year_unit_names = year_unit.get_value("names")
    for i in range(months_across):
        if current_month <= len(year_unit_names):
            # Get the month name from year_unit.names
            month_name = year_unit_names[current_month - 1]
            total_width = week_length * 3
            # Calculate padding based on the length of the month name
            padding_total = total_width - len(month_name)
            padding_left = padding_total // 2
            padding_right = padding_total - padding_left
            # Build the centered month name with padding
            colored_centered_month_name = (
                " " * padding_left + f"\033[34m{month_name}\033[0m" + " " * padding_right
            )
            month_names.append(colored_centered_month_name)
            current_month += 1
        else:
            # Empty space for months beyond those defined in year_unit.names
            month_names.append(" " * (week_length * 3))
    print_row(month_names, width=week_length * 3)


def print_weekday_headers(week_unit, months_across, week_length):
    """Prints the weekday headers for a row of months."""
    weekday_header = " ".join(["\033[33m" + name[:2] + "\033[0m" for name in week_unit.names])
    weekday_headers = [weekday_header.ljust(week_length * 3)] * months_across
    print_row(weekday_headers, width=week_length * 3)


@dataclass
class TimeRange:  # Data class to hold time ranges
    start: float
    end: float


def get_time_range(timestamp, unit):
    start = unit.get_value("start", timestamp)
    end = start + unit.get_value("length", timestamp)
    return TimeRange(start, end)


def format_day(
    day_num, is_current_month, current_week_range, current_day_timestamp, day_unit, timestamp
):  # Function to format day string
    day_str = f"{day_num:2}"
    if is_current_month:
        if current_week_range.start <= current_day_timestamp < current_week_range.end:
            if day_unit.get_value("start", current_day_timestamp) == day_unit.get_value(
                "start", timestamp
            ):
                day_str = f"\033[41m{day_str}\033[0m"
            else:
                day_str = f"\033[96m{day_str}\033[0m"
        else:
            day_str = f"\033[32m{day_str}\033[0m"
    return day_str


def get_month_week_days(
    days,
    month_starts,
    month_ends,
    first_day_weekdays,
    week_length,
    current_week_range,
    current_month_range,
    day_unit,
    i,
    timestamp,
):
    month_week_days = []
    for day_of_week in range(week_length):
        if days[i] <= month_ends[i].day:
            if day_of_week >= first_day_weekdays[i]:
                current_date = month_starts[i].replace(day=days[i])
                current_day_timestamp = current_date.timestamp()
                is_current_month = (
                    current_month_range.start <= current_day_timestamp < current_month_range.end
                )
                day_str = format_day(
                    days[i],
                    is_current_month,
                    current_week_range,
                    current_day_timestamp,
                    day_unit,
                    timestamp,
                )
                month_week_days.append(day_str)
                days[i] += 1
            else:
                month_week_days.append("  ")
        else:
            month_week_days.append("  ")
    return " ".join(month_week_days)


def print_week_row(
    timestamp,
    days,
    month_starts,
    month_ends,
    first_day_weekdays,
    week_length,
    month_unit,
    week_unit,
    day_unit,
):
    week_row = []
    current_week_range = get_time_range(timestamp, week_unit)
    current_month_range = get_time_range(timestamp, month_unit)
    for i in range(len(month_starts)):
        week_days_str = get_month_week_days(
            days,
            month_starts,
            month_ends,
            first_day_weekdays,
            week_length,
            current_week_range,
            current_month_range,
            day_unit,
            i,
            timestamp,
        )
        week_row.append(week_days_str.ljust(week_length * 3))
    print_row(week_row, width=week_length * 3)


def print_year_calendar(timestamp, year_unit, month_unit, week_unit, day_unit):
    timezone = get_timezone(year_unit, timestamp)
    year_start = datetime.datetime.fromtimestamp(
        year_unit.get_value("start", timestamp), tz=timezone
    )
    week_length = week_unit.get_value("length", timestamp) // day_unit.get_value(
        "length", timestamp
    )
    months_across = 3
    total_width = months_across * (week_length * 3 + 3)
    year_str = str(year_start.year)
    padding = (total_width - len(year_str)) // 2
    print(" " * padding + "\033[1;31m" + year_str + "\033[0m " * padding)
    print()
    current_month = 1
    year_unit_names = year_unit.get_value("names")
    total_months = len(year_unit_names)
    while current_month <= total_months:
        print_month_headers(year_start, current_month, months_across, week_length, year_unit)
        print_weekday_headers(week_unit, months_across, week_length)
        days, month_starts, month_ends, first_day_weekdays = get_month_data(
            timestamp, year_start, current_month, months_across, month_unit, week_unit, day_unit
        )
        max_weeks = 0
        for i in range(len(month_starts)):
            weeks_in_month = (month_ends[i].day + first_day_weekdays[i] + 6) // 7
            max_weeks = max(max_weeks, weeks_in_month)

        for _ in range(max_weeks):
            print_week_row(
                timestamp,
                days,
                month_starts,
                month_ends,
                first_day_weekdays,
                week_length,
                month_unit,
                week_unit,
                day_unit,
            )
            for i in range(len(first_day_weekdays)):
                if days[i] <= month_ends[i].day:
                    # Calculate the weekday index for the next day
                    next_day_timestamp = month_starts[i].replace(day=days[i]).timestamp()
                    first_day_weekdays[i] = (
                        get_day_of_week(next_day_timestamp, week_unit, day_unit) % week_length
                    )
                else:
                    first_day_weekdays[i] = 0  # No more days in this month

        current_month += months_across
        print()  # Add an empty line between month rows


def main():
    hy_file_path = "resources/units.hy"
    units_data = evaluate_hy_file(hy_file_path)
    timestamp = time.time()
    timestamp = datetime.datetime(2025, 1, 15, 0, 0, 0, tzinfo=datetime.timezone.utc).timestamp()
    # timestamp = datetime.datetime(2025,1,16,0,0,0,tzinfo=datetime.timezone.utc).timestamp()
    # timestamp = datetime.datetime(2025, 1, 16, 0, 0, 1, tzinfo=datetime.timezone.utc).timestamp()
    # timestamp = datetime.datetime(2024,6,27,23,59,59,tzinfo=datetime.timezone.utc).timestamp()
    units = process_units(units_data, timestamp)
    for unit in units.values():
        print(f"Unit: {unit.name}")
        print(f"  length: {unit.get_value('length', timestamp)/86400}")
        print(f"  timezone: {unit.get_value('timezone')/3600}")
        if unit.start:
            print(
                f"  start: {datetime.datetime.fromtimestamp(unit.get_value('start', timestamp), tz=datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S %z')}"
            )
        print(f"  start: {unit.get_value('start', timestamp)}")
        print(f"  names: {unit.get_value('names')}")
        print(f"  index: {unit.get_value('index', timestamp)}")
        if unit.names:
            print(f"  name: {unit.get_value('names')[unit.get_value('index', timestamp)]}")
        # Access other properties similarly: unit.timezone, unit.start, etc.
        # print_month_calendar(timestamp, units["year"], units["month"], units["week10"], units["day"])
        # # print_calendar(units["month"], units["week10"], units["day"])
        # print_year_calendar(timestamp, units["year"], units["month"], units["week7"], units["day"])
    calendar = Calendar(timestamp, units)
    calendar.print_year_calendar()


if __name__ == "__main__":
    main()
