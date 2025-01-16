import time
import datetime
from dataclasses import dataclass
import hy
from hy.models import Expression, Symbol, String, Integer, List, Lazy
from hy.compiler import hy_eval
from decimal import Decimal
from typing import Optional


@dataclass
class Unit:
    name: str
    length: Decimal = Decimal(0)
    start: Decimal = Decimal(0)
    names: Optional[List[str]] = None
    timezone: Decimal = Decimal(0)
    offset: int = 0
    index: int = 0

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


def resolve_unit_property(expr, units, current_unit=None, timestamp=None):
    """Recursively resolves unit properties, handling inter-unit references."""
    if isinstance(expr, Integer):
        return int(expr)
    elif isinstance(expr, String):
        return str(expr)
    elif isinstance(expr, Symbol):
        sym_str = str(expr)

        if "." in sym_str:  # Handle inter-unit references
            unit_name, prop_name = sym_str.split(".", 1)
            if unit_name in units and hasattr(units[unit_name], prop_name):
                return getattr(units[unit_name], prop_name)
            elif unit_name in units:  # Handle circular or multi-step dependencies
                return resolve_unit_property(
                    expr, units, current_unit=current_unit, timestamp=timestamp
                )  # Pass the current_unit
            else:
                dependent_unit = Unit(name=unit_name)
                units[unit_name] = dependent_unit
                return resolve_unit_property(
                    expr, units, current_unit=current_unit, timestamp=timestamp
                )  # Pass the current_unit

        # Check if symbol matches a unit property of the current unit
        elif current_unit and hasattr(current_unit, sym_str):
            return getattr(current_unit, sym_str)
        elif sym_str in units:  # Handle referencing a unit by name
            return units[sym_str]
        try:  # Attempt conversion for potential numeric symbols
            return int(sym_str)
        except ValueError:
            return sym_str  # otherwise return as string
    elif isinstance(expr, List):
        return [
            resolve_unit_property(item, units, current_unit, timestamp=timestamp) for item in expr
        ]
    elif isinstance(expr, Expression):
        locals_dict = dict(
            __builtins__=globals()["__builtins__"],
            time=time,
            datetime=datetime,
            TIMESTAMP=timestamp,
            get_day_of_week=get_day_of_week,
            **units,
        )

        if current_unit:
            locals_dict["self"] = current_unit

        return hy_eval(expr, locals=locals_dict)
    else:
        return expr


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
        if not unit.index and unit.names and unit.length and unit.start:
            unit.index = (
                int((timestamp - unit.start) / unit.length * len(unit.names)) if unit.length else 0
            )

    return units


def print_calendar(month_unit, week_unit, day_unit):
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


def get_month_data(year_start, current_month, months_across, week_unit, day_unit):
    """Calculates and returns month-related data for a row of months."""
    days = [1] * months_across
    month_starts = []
    month_ends = []
    first_day_weekdays = []
    week_day_length = week_unit.length // day_unit.length

    for i in range(months_across):
        m = current_month + i
        if 1 <= m <= 12:
            month_start = datetime.datetime(year_start.year, m, 1)
            month_end = month_start.replace(month=m % 12 + 1, day=1) - datetime.timedelta(days=1)
            month_ends.append(month_end)
            month_starts.append(month_start)
            first_day_weekday = (
                get_day_of_week(month_start.timestamp(), week_unit, day_unit) % week_day_length
            )
            first_day_weekdays.append(first_day_weekday)
    return days, month_starts, month_ends, first_day_weekdays


def print_month_headers(year_start, current_month, months_across):
    """Prints the month headers for a row of months."""
    month_names_row = []
    for _ in range(months_across):
        if current_month <= 12:
            month_start = datetime.datetime(year_start.year, current_month, 1)
            month_names_row.append(month_start.strftime("%B").center(20))
            current_month += 1
        else:
            month_names_row.append("".center(20))
    print("   ".join(month_names_row))


def print_weekday_headers(week_unit, months_across):
    """Prints the weekday headers for a row of months."""
    week_header = " ".join([name[:2] for name in week_unit.names]) + "   "
    print(f"{week_header:20s}" * months_across)


def print_week_row(days, month_starts, month_ends, first_day_weekdays, week_length):
    week_row = []
    for i in range(len(month_starts)):  # Use correct index range

        month_week_days = []
        if (
            days[i] <= month_ends[i].day + 1
        ):  # change here: print spaces for last week if applicable
            for w in range(week_length):
                if days[i] <= month_ends[i].day:  # changed
                    if w >= first_day_weekdays[i]:
                        day_str = f"{days[i]:2}"
                        month_week_days.append(day_str)
                        days[i] += 1
                    elif w < first_day_weekdays[i] and days[i] == 1:  # Pad only the first week
                        month_week_days.append("  ")  # Correct padding string
                    else:  # changed
                        month_week_days.append("  ")
                elif days[i] > month_ends[i].day:  # Apply padding for remaining days of the month
                    month_week_days.append("  ")
            week_row.append(" ".join(month_week_days))
    print("   ".join(week_row))


def print_year_calendar(year_unit, week_unit, day_unit):
    """Prints the yearly calendar."""
    year_start = datetime.datetime.fromtimestamp(year_unit.start)
    week_length = week_unit.length // day_unit.length

    print(f"\n{year_start.year}\n")

    months_across = 3
    current_month = 1

    while current_month <= 12:
        print_month_headers(year_start, current_month, months_across)
        print_weekday_headers(week_unit, months_across)

        days, month_starts, month_ends, first_day_weekdays = get_month_data(
            year_start, current_month, months_across, week_unit, day_unit
        )
        print(days, month_starts, month_ends, first_day_weekdays)

        max_weeks = 0
        for i in range(len(month_starts)):
            weeks_in_month = (month_ends[i].day + first_day_weekdays[i] + 6) // 7
            max_weeks = max(max_weeks, weeks_in_month)

        for _ in range(max_weeks):
            print_week_row(days, month_starts, month_ends, first_day_weekdays, week_length)
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
    timestamp = datetime.datetime(2025,1,16,0,0,1,tzinfo=datetime.timezone.utc).timestamp()
    units = process_units(units_data, timestamp)

    for unit in units.values():
        print(f"Unit: {unit.name}")
        print(f"  length: {unit.length/86400}")
        print(f"  timezone: {unit.timezone/3600}")
        if unit.start:
            print(
                f"  start: {datetime.datetime.fromtimestamp(unit.start, tz=datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S %z')}"
            )
        print(f"  start: {unit.start}")
        print(f"  names: {unit.names}")
        print(f"  index: {unit.index}")
        if unit.names:
            print(f"  name: {unit.names[unit.index]}")
        # Access other properties similarly: unit.timezone, unit.start, etc.


    print_calendar(units["month"], units["week7"], units["day"])
    # print_calendar(units["month"], units["week10"], units["day"])
    # print_year_calendar(units["year"], units["week7"], units["day"])


if __name__ == "__main__":
    main()
