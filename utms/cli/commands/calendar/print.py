from time import time

from ....core.calendar.registry import CalendarRegistry
from ..core import Command, CommandManager
from ....core import Calendar

def print_calendar(config):
    timestamp = time()
    for unit in config._calendar_units.values():
        unit.calculate_index(timestamp)

    CalendarRegistry.initialize(config._calendar_units, config._calendars)
    calendar = Calendar("gregorian", timestamp)
    calendar.print_year_calendar()


def register_calendar_print_command(command_manager: CommandManager) -> None:
    command = Command(
        "calendar", "print", lambda args: print_calendar(command_manager.config), is_default=True
    )
    command.set_help("Print calendar")
    command.set_description("print_calendar")
    # Add the arguments for this command
    # add_key_argument(command)
    command_manager.register_command(command)
