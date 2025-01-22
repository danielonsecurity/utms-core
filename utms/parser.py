import datetime
import time
import uuid
from dataclasses import dataclass
from decimal import Decimal
from types import FunctionType
from typing import Optional

import hy
from hy.compiler import hy_eval
from hy.models import Expression, Integer, Lazy, List, String, Symbol

from utms.core import Calendar, CalendarUnit, process_units, CalendarRegistry
from utms.resolvers import evaluate_hy_file
from utms.utils import get_day_of_week, get_timezone, set_log_level, get_logger

logger = get_logger("parser")


from utms.core.calendar.unit_loader import parse_calendar_definitions, get_calendar_units

def main():
    set_log_level("DEBUG")
    set_log_level("WARNING")
    hy_file_path = "resources/units.hy"
    units_data = evaluate_hy_file(hy_file_path)
    
    # # timestamp = time.time()
    # # timestamp = datetime.datetime(2024, 6, 17, 12, 0, 0, tzinfo=datetime.timezone.utc).timestamp() # Leap day in IFT
    # # timestamp = datetime.datetime(2025,1,16,0,0,0,tzinfo=datetime.timezone.utc).timestamp()
    # # timestamp = datetime.datetime(2025, 1, 16, 0, 0, 1, tzinfo=datetime.timezone.utc).timestamp()
    # # timestamp = datetime.datetime(2024,6,27,23,59,59,tzinfo=datetime.timezone.utc).timestamp()
    timestamp = datetime.datetime(2025, 6, 19, 12, 0, 0, tzinfo=datetime.timezone.utc).timestamp()
    units = process_units(units_data, timestamp)

    calendars = parse_calendar_definitions(units_data)
    logger.debug(f"Processed calendars: {list(calendars.keys())}")

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
    CalendarRegistry.initialize(units, calendars)
    calendar = Calendar("gregorian", timestamp)
    calendar.print_year_calendar()
    # calendar = Calendar("gregorian-sunday", timestamp)
    # calendar.print_year_calendar()
    # calendar = Calendar("week10", timestamp)
    # calendar.print_year_calendar()
    # calendar = Calendar("ifc", timestamp)
    # calendar.print_year_calendar()


if __name__ == "__main__":
    main()
