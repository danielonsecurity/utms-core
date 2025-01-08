"""
Module for registering the daytime timetable command in the UTMS CLI system.

This module defines the function `register_daytime_timetable_command`, which registers
the `daytime timetable` command to the UTMS CLI. The command outputs a formatted table
that maps decimal time units to duodecimal time units.

Imports:
    - `Command`, `CommandManager`: Command-related classes used to register and manage commands.
    - `generate_time_table`: Utility function to generate the time table.

Exports:
    - `register_daytime_timetable_command`: Function to register the daytime timetable command.
"""

from utms.cli.commands.core import Command, CommandManager
from utms.utils import generate_time_table


def register_daytime_timetable_command(command_manager: CommandManager) -> None:
    """
    Registers the 'daytime timetable' command with the given command manager.

    This function creates a new `Command` for generating and printing a formatted table
    that maps decimal time units to duodecimal time units. The command is registered as
    the default action for the `daytime` command.

    Args:
        command_manager (CommandManager): The manager responsible for
        registering commands in the UTMS CLI system.

    Returns:
        None
    """
    command = Command(
        "daytime", "timetable", lambda _: print(generate_time_table()), is_default=True
    )
    command.set_help("Prints a formatted table mapping decimal to duodecimal day time units")
    command.set_description("Prints a formatted table mapping decimal to duodecimal day time units")

    command_manager.register_command(command)
