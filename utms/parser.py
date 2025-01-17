import datetime
import time
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

import hy
from hy.compiler import hy_eval
from hy.models import Expression, Integer, Lazy, List, String, Symbol


class Unit:
    def __init__(self, name, **kwargs):
        self.name: str = name
        self.length: Decimal = kwargs.get("length", Decimal(0))
        self.start: Decimal = kwargs.get("start", Decimal(0))
        self.names: Optional[List[str]] = kwargs.get("names", None)
        self.timezone: Decimal = kwargs.get("timezone", Decimal(0))
        self.offset: int = kwargs.get("offset", 0)
        self.index: int = kwargs.get("index", 0)

    def __iter__(self):
        for value in self.__dict__.values():  # Iterate through attributes
            yield value

    def get_length(self, timestamp):
        if callable(self.length):
            return self.length(timestamp)
        return self.length

    def get_start(self, timestamp):
        if callable(self.start):
            return self.start(timestamp)
        return self.start

    def get_names(self, timestamp):
        if callable(self.names):
            return self.names(timestamp)
        return self.names

    def get_timezone(self, timestamp):
        if callable(self.timezone):
            return self.timezone(timestamp)
        return self.timezone

    def get_offset(self, timestamp):
        if callable(self.offset):
            return self.offset(timestamp)
        return self.offset

    def get_index(self, timestamp):
        if callable(self.index):
            return self.index(timestamp)
        return self.index


def get_day_of_week(timestamp: float, week_unit: Unit, day_unit: Unit) -> int:
    timezone = datetime.timezone(datetime.timedelta(seconds=float(week_unit.timezone)))
    reference_timestamp = (
        datetime.datetime(1970, 1, 1, tzinfo=timezone) + datetime.timedelta(days=week_unit.offset)
    ).timestamp()

    total_days_elapsed = (Decimal(timestamp) - Decimal(reference_timestamp)) // day_unit.length
    day_of_week = int(total_days_elapsed % (week_unit.length // day_unit.length))

    return day_of_week


def evaluate_hy_file(hy_file_path):
    """Evaluates the HyLang file and returns the resulting data structures."""
    with open(hy_file_path, "r") as file:
        hy_code = file.read()
    return hy.read_many(hy_code)


def _resolve_symbol(expr, units, current_unit, timestamp):
    """Resolves a Symbol, handling inter-unit references."""
    sym_str = str(expr)

    if "." in sym_str:  # Inter-unit references
        unit_name, prop_name = sym_str.split(".", 1)
        if unit_name in units and hasattr(units[unit_name], prop_name):
            return getattr(units[unit_name], prop_name)
        elif unit_name in units:  # Circular/multi-step dependencies
            return resolve_unit_property(expr, units, current_unit, timestamp)
        else:  # Unit not yet defined, create placeholder
            dependent_unit = Unit(name=unit_name)
            units[unit_name] = dependent_unit
            return resolve_unit_property(expr, units, current_unit, timestamp)

    elif current_unit and hasattr(current_unit, sym_str):  # changed: incorrect check
        return getattr(current_unit, sym_str)
    elif sym_str in units:  # Referencing a unit by name
        return units[sym_str]
    try:  # Try converting to int
        return int(sym_str)
    except ValueError:
        return sym_str  # Return as string


def _resolve_list(expr, units, current_unit, timestamp):
    return [resolve_unit_property(item, units, current_unit, timestamp) for item in expr]


def _resolve_expression(expr, units, current_unit, timestamp):
    resolved_subexprs = []
    for subexpr in expr:
        if isinstance(subexpr, Expression):
            resolved = resolve_unit_property(subexpr, units, current_unit, timestamp)
            if callable(resolved):
                resolved_subexprs.append(subexpr)
            else:
                resolved_subexprs.append(resolved)
        # elif isinstance(subexpr, List):
        #     print(subexpr)
        #     breakpoint()
        #     resolved = resolve_unit_property(subexpr, units, current_unit, timestamp)
        else:
            print(subexpr)
            resolved_subexprs.append(subexpr)

    locals_dict = dict(
        __builtins__=globals()["__builtins__"],
        time=time,
        datetime=datetime,
        get_day_of_week=get_day_of_week,
        timestamp=timestamp,
        **units,
    )

    if current_unit:
        locals_dict["self"] = current_unit
    try:
        print(f"0: {resolved_subexprs}")

        value = hy_eval(Expression(resolved_subexprs), locals_dict)
    except NameError:
        value = Expression(resolved_subexprs)

    except Exception as e:  # added more specific exception handling
        if "object is not callable" in str(e):

            return Expression(resolved_subexprs)

        else:
            raise e  # re-raise exceptions
    return value


def resolve_unit_property(expr, units, current_unit=None, timestamp=None):
    """Recursively resolves unit properties."""

    if isinstance(expr, Integer):
        return int(expr)
    elif isinstance(expr, String):
        return str(expr)
    elif isinstance(expr, Symbol):
        print(f"symbol:{expr}")
        return _resolve_symbol(expr, units, current_unit, timestamp)
    elif isinstance(expr, List):
        print(f"list:{expr}")
        return _resolve_list(expr, units, current_unit, timestamp)
    elif isinstance(expr, Expression):
        print(f"expression:{expr}")
        return _resolve_expression(expr, units, current_unit, timestamp)
    else:
        print(f"expr:{expr}")
        return expr


# def resolve_unit_property(expr, units, current_unit=None, timestamp=None):
#     """Recursively resolves unit properties, handling inter-unit references."""
#     if isinstance(expr, Integer):
#         return int(expr)
#     elif isinstance(expr, String):
#         return str(expr)
#     elif isinstance(expr, Symbol):
#         sym_str = str(expr)

#         if "." in sym_str:  # Handle inter-unit references
#             unit_name, prop_name = sym_str.split(".", 1)
#             if unit_name in units and hasattr(units[unit_name], prop_name):
#                 return getattr(units[unit_name], prop_name)
#             elif unit_name in units:  # Handle circular or multi-step dependencies
#                 return resolve_unit_property(
#                     expr, units, current_unit=current_unit, timestamp=timestamp
#                 )  # Pass the current_unit
#             else:
#                 dependent_unit = Unit(name=unit_name)
#                 units[unit_name] = dependent_unit
#                 return resolve_unit_property(
#                     expr, units, current_unit=current_unit, timestamp=timestamp
#                 )  # Pass the current_unit

#         # Check if symbol matches a unit property of the current unit
#         elif current_unit and hasattr(current_unit, sym_str):
#             return getattr(current_unit, sym_str)
#         elif sym_str in units:  # Handle referencing a unit by name
#             return units[sym_str]
#         try:  # Attempt conversion for potential numeric symbols
#             return int(sym_str)
#         except ValueError:
#             return sym_str  # otherwise return as string
#     elif isinstance(expr, List):
#         return [
#             resolve_unit_property(item, units, current_unit, timestamp=timestamp) for item in expr
#         ]
#     elif isinstance(expr, Expression):
#         resolved_subexprs = []
#         for subexpr in expr:
#             if isinstance(subexpr, Expression):
#                 resolved_subexprs.append(resolve_unit_property(subexpr, units, current_unit, timestamp))
#             else:
#                 resolved_subexprs.append(subexpr)
#         locals_dict = dict(
#             __builtins__=globals()["__builtins__"],
#             time=time,
#             datetime=datetime,
#             TIMESTAMP=timestamp,
#             get_day_of_week=get_day_of_week,
#             **units,
#         )

#         if current_unit:
#             locals_dict["self"] = current_unit
#         # print(expr)
#         # print(resolved_subexprs)
#         try:
#             value = hy_eval(Expression(resolved_subexprs), locals_dict)
#         except NameError:
#             value = Expression(resolved_subexprs)
#         # print(value)
#         return value
#     else:
#         return expr


def process_units(units_data, timestamp):
    units = {}
    for unit_def_expr in units_data:
        if not isinstance(unit_def_expr, Expression) or unit_def_expr[0] != Symbol("defunit"):
            raise ValueError("Invalid unit definition format.")

        unit_definitions = unit_def_expr[1:]

        unit_name = str(unit_definitions[0])
        unit_kwargs = {}

        for item in unit_definitions[1:]:
            if isinstance(item, Expression):
                prop_name = str(item[0])
                prop_value = item[1]  # Store the raw Hy expression
                unit_kwargs[prop_name] = prop_value
            else:
                raise ValueError(f"Unexpected item type: {type(item)}")

        units[unit_name] = Unit(name=unit_name, **unit_kwargs)

    # Resolve properties recursively, passing the current unit
    for unit in units.values():
        for prop_name, prop_value in unit.__dict__.items():
            if prop_name != "name":
                resolved_value = resolve_unit_property(prop_value, units, unit, timestamp)
                setattr(unit, prop_name, resolved_value)

    # Calculate index after all properties are resolved
    for unit in units.values():
        if (
            not unit.get_index(timestamp)
            and unit.get_names(timestamp)
            and unit.get_length(timestamp)
            and unit.get_start(timestamp)
        ):
            unit.index = (
                int(
                    (timestamp - unit.get_start(timestamp))
                    / unit.get_length(timestamp)
                    * len(unit.get_names(timestamp))
                )
                if unit.get_length(timestamp)
                else 0
            )

    return units


def print_month_calendar(month_unit, week_unit, day_unit):
    """Prints the calendar, highlighting the current week and day with colors."""

    month_start = datetime.datetime.fromtimestamp(month_unit.start, tz=datetime.timezone.utc)
    month_end_timestamp = month_unit.start + month_unit.length

    week_start_datetime = datetime.datetime.fromtimestamp(week_unit.start, tz=datetime.timezone.utc)
    current_week_start = week_start_datetime.timestamp()
    current_week_end = current_week_start + week_unit.length

    print(f"{month_start.strftime('%B %Y')}:")
    print(" ".join([name[:2] for name in week_unit.names]))
    week_day_length = week_unit.length // day_unit.length

    current_day = month_start.replace(day=1)
    first_day_weekday = (
        get_day_of_week(current_day.timestamp(), week_unit, day_unit) % week_day_length
    )

    print("   " * first_day_weekday, end="")

    day_num = 1
    while current_day.timestamp() < month_end_timestamp:
        if current_week_start <= current_day.timestamp() < current_week_end:

            if current_day.timestamp() == (day_unit.start):  # today
                print(f"\033[41m{day_num:2}\033[0m ", end="")
            else:
                print(f"\033[96m{day_num:2}\033[0m ", end="")
        else:
            print(f"{day_num:2} ", end="")

        if (
            get_day_of_week(current_day.timestamp(), week_unit, day_unit)
        ) % week_day_length == week_day_length - 1:
            print()

        current_day += datetime.timedelta(days=1)
        day_num += 1

    print()


def get_month_data(year_start, current_month, months_across, month_unit, week_unit, day_unit):
    """Calculates and returns month-related data for a row of months."""
    timezone = datetime.timezone(datetime.timedelta(seconds=float(week_unit.timezone)))
    days = [1] * months_across
    month_starts = []
    month_ends = []
    first_day_weekdays = []
    week_day_length = week_unit.length // day_unit.length

    for i in range(months_across):
        m = current_month + i
        if 1 <= m <= 12:
            month_start = datetime.datetime(year_start.year, m, 1, tzinfo=timezone)
            month_end = month_start.replace(month=m % 12 + 1, day=1) - datetime.timedelta(days=1)
            month_ends.append(month_end)
            month_starts.append(month_start)
            first_day_weekday = (
                get_day_of_week(month_start.timestamp(), week_unit, day_unit) % week_day_length
            )
            first_day_weekdays.append(first_day_weekday)
    return days, month_starts, month_ends, first_day_weekdays


def print_month_headers(year_start, current_month, months_across, week_length):
    """Prints month headers, aligned with day grids."""
    month_names_row = []
    for _ in range(months_across):
        if current_month <= 12:
            month_start = datetime.datetime(year_start.year, current_month, 1)
            month_name = month_start.strftime("%B")
            # Calculate centering based on week_length
            padding = (week_length * 3 - len(month_name)) // 2  # changed: fixed calculation error
            centered_month_name = (
                " " * padding + "\033[34m" + month_name + "\033[0m " * padding
            )  # Center the month name
            month_names_row.append(centered_month_name)
            current_month += 1
        else:
            # Padding for empty cells in the last row
            month_names_row.append(" " * (week_length * 3))  # changed

    print("   ".join(month_names_row))


def print_weekday_headers(week_unit, months_across):
    """Prints the weekday headers for a row of months."""
    week_header = " ".join(["\033[33m" + name[:2] + "\033[0m" for name in week_unit.names]) + "   "
    print(f"{week_header:20s}" * months_across)


def print_week_row(
    days, month_starts, month_ends, first_day_weekdays, week_length, month_unit, week_unit, day_unit
):
    week_row = []
    current_week_start = week_unit.start
    current_week_end = week_unit.start + week_unit.length
    current_month_start = month_unit.start
    current_month_end = month_unit.start + month_unit.length
    for i in range(len(month_starts)):  # Use correct index range

        month_week_days = []
        if (
            days[i] <= month_ends[i].day + 1
        ):  # change here: print spaces for last week if applicable
            for w in range(week_length):
                if days[i] <= month_ends[i].day:  # changed
                    if w >= first_day_weekdays[i]:
                        current_date = month_starts[i].replace(day=days[i])
                        day_str = f"{days[i]:2}"
                        if current_month_start <= current_date.timestamp() < current_month_end:
                            if current_week_start <= current_date.timestamp() < current_week_end:
                                if current_date.timestamp() == day_unit.start + day_unit.timezone:
                                    day_str = f"\033[41m{day_str}\033[0m"
                                else:
                                    day_str = f"\033[96m{day_str}\033[0m"
                            else:
                                day_str = f"\033[32m{day_str}\033[0m"
                        month_week_days.append(day_str)
                        days[i] += 1
                    elif w < first_day_weekdays[i] and days[i] == 1:
                        month_week_days.append("  ")
                    else:  # changed
                        month_week_days.append("  ")
                elif days[i] > month_ends[i].day:
                    month_week_days.append("  ")
            week_row.append(" ".join(month_week_days))
    print("   ".join(week_row))


def print_year_calendar(year_unit, month_unit, week_unit, day_unit):
    """Prints the yearly calendar."""
    year_start = datetime.datetime.fromtimestamp(year_unit.start)
    week_length = week_unit.length // day_unit.length

    months_across = 3
    total_width = months_across * (
        week_length * 3 + 3
    )  # changed: added spaces between months to calculation of total width
    year_str = str(year_start.year)
    padding = (total_width - len(year_str)) // 2
    print(
        " " * padding + "\033[1;31m" + year_str + "\033[0m " * padding
    )  # added: center the year string
    print()

    current_month = 1

    while current_month <= 12:
        print_month_headers(year_start, current_month, months_across, week_length)
        print_weekday_headers(week_unit, months_across)

        days, month_starts, month_ends, first_day_weekdays = get_month_data(
            year_start, current_month, months_across, month_unit, week_unit, day_unit
        )
        # print(days, month_starts, month_ends, first_day_weekdays)

        max_weeks = 0
        for i in range(len(month_starts)):
            weeks_in_month = (month_ends[i].day + first_day_weekdays[i] + 6) // 7
            max_weeks = max(max_weeks, weeks_in_month)

        for _ in range(max_weeks):
            print_week_row(
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
                if days[i] > 1 and (
                    days[i] > month_ends[i].day + 1
                    or get_day_of_week(
                        month_starts[i].replace(day=days[i] - 1).timestamp(), week_unit, day_unit
                    )
                    == (len(week_unit.names) - 1) % week_length
                ):
                    first_day_weekdays[i] = 0

        current_month += months_across


def main():
    hy_file_path = "resources/units.hy"
    units_data = evaluate_hy_file(hy_file_path)
    timestamp = time.time()
    # timestamp = datetime.datetime(2025,1,15,23,59,59,tzinfo=datetime.timezone.utc).timestamp()
    # timestamp = datetime.datetime(2025,1,16,0,0,0,tzinfo=datetime.timezone.utc).timestamp()
    # timestamp = datetime.datetime(2025, 1, 16, 0, 0, 1, tzinfo=datetime.timezone.utc).timestamp()
    # timestamp = datetime.datetime(2024,6,27,23,59,59,tzinfo=datetime.timezone.utc).timestamp()
    units = process_units(units_data, timestamp)

    for unit in units.values():
        print(f"Unit: {unit.name}")
        print(f"  length: {unit.get_length(timestamp)/86400}")
        print(f"  timezone: {unit.get_timezone(timestamp)/3600}")
        if unit.start:
            print(
                f"  start: {datetime.datetime.fromtimestamp(unit.get_start(timestamp), tz=datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S %z')}"
            )
        print(f"  start: {unit.get_start(timestamp)}")
        print(f"  names: {unit.get_names(timestamp)}")
        print(f"  index: {unit.get_index(timestamp)}")
        if unit.names:
            print(f"  name: {unit.get_names(timestamp)[unit.index]}")
        # Access other properties similarly: unit.timezone, unit.start, etc.

    # print_month_calendar(units["month"], units["week10"], units["day"])
    # print_calendar(units["month"], units["week10"], units["day"])
    print_year_calendar(units["year"], units["month13"], units["week7"], units["day"])


if __name__ == "__main__":
    main()
