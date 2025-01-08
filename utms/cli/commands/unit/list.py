"""
Module for registering and handling the 'unit list' command in the UTMS CLI system.

This module defines the function `register_unit_list_command` to
register the 'unit list' command.  It lists all available time units
configured in the system.

Imports:
    - `Command`, `CommandManager`: For managing commands in the CLI system.

Exports:
    - `register_unit_list_command`: Function to register the unit list command.
"""

from utms.cli.commands.core import Command, CommandManager


def register_unit_list_command(command_manager: CommandManager) -> None:
    """
    Registers the 'unit list' command with the given command manager.

    This function creates and registers a command to list all
    available time units in the system.  The command is marked as the
    default action.

    Args:
        command_manager (CommandManager): The manager responsible for
        registering commands in the UTMS CLI system.

    Returns:
        None
    """
    units_manager = command_manager.config.units
    command = Command("unit", "list", lambda _: units_manager.print(), is_default=True)
    command.set_help("List all time units")
    command.set_description("List all time units")
    command_manager.register_command(command)
