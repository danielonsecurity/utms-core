"""
Module for registering and handling the 'unit table' command in the UTMS CLI system.

This module defines the function `register_unit_table_command` to
register the 'unit table' command.  It displays a conversion table for
a specific unit, with optional parameters to customize the number of
rows and columns.

Imports:
    - `Command`, `CommandManager`: For managing commands in the CLI system.

Exports:
    - `register_unit_table_command`: Function to register the unit table command.
"""

from utms.cli.commands.core import Command, CommandManager


def register_unit_table_command(command_manager: CommandManager) -> None:
    """
    Registers the 'unit table' command with the given command manager.

    This function creates and registers a command to display a unit
    conversion table for a specific unit.  It allows the user to
    specify the number of rows and columns for the table. The command
    is marked as the default action.

    Args:
        command_manager (CommandManager): The manager responsible for
        registering commands in the UTMS CLI system.

    Returns:
        None
    """
    units_manager = command_manager.config.units
    command = Command(
        "unit",
        "table",
        lambda args: units_manager.print_conversion_table(args.unit, args.columns, args.rows),
    )
    command.set_help("Display unit conversion table")
    command.set_description(
        """
    Display a conversion table for a specific unit. The parameters are optional.

    Examples:
      unit table s
      unit table m 5
      unit table h 3 10
    """
    )

    # Add the arguments for this command
    command.add_argument(
        "unit",
        type=str,
        nargs="?",
        default="s",
        help='The base unit for the conversion table ("s", "m", etc). Defaults to "s" if omitted.',
    )
    command.add_argument(
        "columns",
        type=int,
        nargs="?",
        default=5,
        help="Number of columns before/after the base unit (default=5)",
    )
    command.add_argument(
        "rows",
        type=int,
        nargs="?",
        default=100,
        help="Number of rows before/after the base unit (default=100)",
    )

    command_manager.register_command(command)
