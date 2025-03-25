"""Module for registering and handling the 'unit convert' command in the UTMS
CLI system.

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

from ..core import Command, CommandManager
from .helper import (
    add_full_argument,
    add_plt_argument,
    add_precision_argument,
    add_raw_argument,
    add_source_unit_argument,
    add_target_unit_argument,
    add_value_argument,
)


def register_unit_convert_command(command_manager: CommandManager) -> None:
    """Registers the 'unit convert' command with the given command manager.

    This function creates and registers a command to convert a given value between units.
    The target unit is optional: if omitted, the system will perform
    conversions to all available units.

    Args:
        command_manager (CommandManager): The manager responsible for
        registering commands in the UTMS CLI system.

    Returns:
        None
    """
    units_component = command_manager.config.units
    command = Command(
        "unit",
        "convert",
        units_component.convert,
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
    add_value_argument(command)
    add_source_unit_argument(command)
    add_target_unit_argument(command)
    add_full_argument(command)
    add_precision_argument(command)
    add_raw_argument(command)
    add_plt_argument(command)
    command_manager.register_command(command)
