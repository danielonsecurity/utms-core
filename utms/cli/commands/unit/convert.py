"""
Module for registering and handling the 'unit convert' command in the UTMS CLI system.

This module defines the function `register_unit_convert_command` to
register the 'unit convert' command.  It allows converting a numerical
value from one unit to another. The target unit is optional and, if
omitted, the conversion will display all possible unit conversions.

Imports:
    - `Decimal`: For handling precise numerical values during unit conversion.
    - `Command`, `CommandManager`: For managing commands in the CLI system.

Exports:
    - `register_unit_convert_command`: Function to register the unit conversion command.
"""

from decimal import Decimal

from utms.cli.commands.core import Command, CommandManager


def register_unit_convert_command(command_manager: CommandManager) -> None:
    """
    Registers the 'unit convert' command with the given command manager.

    This function creates and registers a command to convert a given value between units.
    The target unit is optional: if omitted, the system will perform
    conversions to all available units.

    Args:
        command_manager (CommandManager): The manager responsible for
        registering commands in the UTMS CLI system.

    Returns:
        None
    """
    units_manager = command_manager.config.units
    command = Command(
        "unit",
        "convert",
        lambda args: units_manager.convert_units(
            Decimal(args.value), args.source_unit, args.target_unit
        ),
    )
    command.set_help("Convert value between units")
    command.set_description(
        """
Convert a value from one unit to another. The `target_unit` is optional:

Examples:
  unit convert 60 s m
  unit convert 1e6 h Y
  unit convert 2500 m
    """
    )

    # Add the arguments for this command
    command.add_argument(
        "value",
        type=float,
        help="The numerical value to be converted",
    )
    command.add_argument(
        "source_unit",
        help="The unit of the value to be converted",
    )
    command.add_argument(
        "target_unit",
        nargs="?",
        help="The desired unit to convert to. If omitted, all units are used (optional)",
    )

    command_manager.register_command(command)
