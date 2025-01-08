"""
Module for registering the daytime conversion command in the UTMS CLI system.

This module defines the function `register_daytime_convert_command`, which registers
the `daytime convert` command to the UTMS CLI. The command allows users to convert
between decimal and duodecimal daytime units.

Imports:
    - `Command`, `CommandManager`: Command-related classes used to register and manage commands.
    - `convert_time`: Utility function for converting time units.

Exports:
    - `register_daytime_convert_command`: Function to register the daytime conversion command.
"""

from utms.cli.commands.core import Command, CommandManager
from utms.utils import convert_time


def register_daytime_convert_command(command_manager: CommandManager) -> None:
    """
    Registers the 'daytime convert' command with the given command manager.

    This function creates a new `Command` for converting between
    decimal and duodecimal daytime units.
    It configures the command's arguments, help text, and description
    before registering it with the provided `CommandManager`.

    Args:
        command_manager (CommandManager): The manager responsible for
        registering commands in the UTMS CLI system.

    Returns:
        None
    """
    command = Command("daytime", "convert", lambda args: print(convert_time(args.value)))
    command.set_help("Convert daytime units")
    command.set_description(
        "Use this command to convert between decimal and duodecimal daytime units"
    )

    # Add the arguments for this command
    command.add_argument(
        "value",
        type=str,
        help="Value to be converted",
    )
    command_manager.register_command(command)
