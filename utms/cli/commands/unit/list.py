"""Module for registering and handling the 'unit list' command in the UTMS CLI
system.

This module defines the function `register_unit_list_command` to
register the 'unit list' command.  It lists all available time units
configured in the system.

Imports:
    - `Command`, `CommandManager`: For managing commands in the CLI system.

Exports:
    - `register_unit_list_command`: Function to register the unit list command.
"""

from ..core import Command, CommandManager
from .helper import add_plt_argument


def register_unit_list_command(command_manager: CommandManager) -> None:
    """Registers the 'unit list' command with the given command manager.

    This function creates and registers a command to list all
    available time units in the system.  The command is marked as the
    default action.

    Args:
        command_manager (CommandManager): The manager responsible for
        registering commands in the UTMS CLI system.

    Returns:
        None
    """
    units_component = command_manager.config.units
    command = Command("unit", "list", units_component.print, is_default=True)
    command.set_help("List all time units")
    command.set_description("List all time units")
    add_plt_argument(command)

    command_manager.register_command(command)
