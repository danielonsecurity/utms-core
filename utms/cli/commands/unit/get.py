"""
Unit retrieval command for the UTMS CLI.

This module provides functionality to retrieve and display information about
a specific unit in the UTMS configuration. It defines the CLI command and its
associated arguments for fetching unit details.

Functions:
    register_unit_get_command(command_manager: CommandManager) -> None
        Registers the 'unit get' command with the CommandManager, enabling
        retrieval of unit details by abbreviation.
"""

from utms.cli.commands.core import Command, CommandManager
from utms.cli.commands.unit.helper import add_abbreviation_argument


def register_unit_get_command(command_manager: CommandManager) -> None:
    """
    Register the 'unit get' command with the CommandManager.

    This function defines a CLI command for retrieving details about a specific
    unit by its abbreviation. The command is registered with the provided
    CommandManager and includes argument configuration.

    Args:
        command_manager (CommandManager): The command manager instance to register
            the 'unit get' command with.
    """
    command = Command(
        "unit", "get", lambda args: print(command_manager.config.units.get_unit(args.abbreviation))
    )
    command.set_help("Print a unit")
    command.set_description("Print a unit")
    # Add the arguments for this command
    add_abbreviation_argument(command)
    command_manager.register_command(command)
