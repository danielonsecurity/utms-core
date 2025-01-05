"""
UTMS Command Line Interface (CLI) Module

This module handles the command-line interface for the UTMS (Universal Time Management System). It
provides functions for parsing and processing arguments, converting units, managing configurations,
and running the clock. It integrates with various helpers and utilities to perform actions based on
user inputs.

The following actions are supported:
- Unit conversion table display (`--unit`).
- Unit conversion between values (`--conv`).
- Day-time conversion (`--dconv`).
- Configuring UTMS (`--config`).
- Generating a timetable (`--timetable`).
- Running the clock (`--clock`).

Functions
---------
- `parse_args()`: Parses command-line arguments and returns a namespace containing the parsed
  arguments.
- `process_args(args: argparse.Namespace)`: Processes the parsed arguments and performs
  corresponding actions.
- `handle_unit_args(unit_args: List[Union[str, int]])`: Displays the unit conversion table based on
  provided arguments.
- `handle_conversion_args(conv_args: List[Union[str, Decimal]])`: Converts between units based on
  provided values and units.
- `handle_dconv_args(dconv_args: List[str])`: Converts day-time values based on provided arguments.
- `handle_config_args(config_args: List[str])`: Configures UTMS based on provided arguments,
  including setting or viewing configuration values.

Modules Imported
----------------
- `argparse`: For parsing command-line arguments.
- `decimal.Decimal`: For working with high-precision decimal values.
- `typing`: For type annotations, including `List` and `Union`.
- `utms.cli.helpers.print_error`: For error handling during CLI operations.
- `utms.clock.run_clock`: For running the clock functionality.
- `utms.config.Config`: For handling UTMS configuration.
- `utms.utils.convert_time`: For day-time conversion functionality.
- `utms.utils.generate_time_table`: For generating a time table.

Usage Example
-------------
To view the unit conversion table for seconds:
    $ utms --unit s

To convert between units:
    $ utms --conv 10 s min

To generate a timetable:
    $ utms --timetable

To configure UTMS settings:
    $ utms --config set key value

"""

import argparse
from datetime import datetime
from decimal import Decimal
from typing import List, Union

from utms import VERSION
from utms.cli.commands import CommandManager, load_default_commands
from utms.cli.helpers import print_error
from utms.clock import run_clock
from utms.config import Config
from utms.utils import convert_time, generate_time_table, print_time, resolve_date

config = Config()


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns
    -------
    Namespace
        An argparse.Namespace object containing the parsed arguments.
    """
    parser = argparse.ArgumentParser(description=f"UTMS CLI version {VERSION}")
    parser.add_argument("--unit", nargs="*", help="Unit conversion table")
    parser.add_argument("--conv", nargs="+", help="Convert value between units")
    parser.add_argument("--dconv", nargs="+", help="Convert day time between units")
    parser.add_argument("--config", nargs="*", help="Configure UTMS")
    parser.add_argument("--clock", action="store_true", help="Run clock")
    parser.add_argument("--timetable", action="store_true", help="Generate timetable")
    parser.add_argument("--help-prompt", action="store_true", help="Prompt help message")
    parser.add_argument("--version", action="store_true", help="Show UTMS version")
    parser.add_argument("input_string", nargs="*", help="String to be resolved into time")
    return parser.parse_args()


def process_args(args: argparse.Namespace) -> bool:
    """
    Processes non-interactive execution based on command-line arguments.

    This function handles all the different argument options like `--unit`, `--conv`, and `--clock`.

    Args:
        args: The parsed arguments from the command line.

    Returns:
        bool: `True` if an argument was processed, `False` otherwise.
    """
    if args.unit or args.unit == []:
        handle_unit_args(args.unit)
    elif args.conv:
        handle_conversion_args(args.conv)
    elif args.dconv:
        handle_dconv_args(args.dconv)
    elif args.config or args.config == []:
        handle_config_args(args.config)
    elif args.timetable:
        print(generate_time_table())
    elif args.clock:
        run_clock()
    elif args.version:
        print(VERSION)
    elif args.help_prompt:
        command_manager = CommandManager()
        load_default_commands(command_manager)
        print(command_manager.generate_help_message())
    elif args.input_string:
        parsed_timestamp = resolve_date(" ".join(args.input_string))
        if isinstance(parsed_timestamp, (datetime, Decimal)):
            print_time(parsed_timestamp, config)
            return True
    else:
        return False
    return True


def handle_unit_args(unit_args: List[Union[str, int]]) -> None:
    """
    Handles the `--unit` argument for displaying unit conversion tables.

    Args:
        unit_args (list): The list of arguments for the `--unit` flag.

    Returns:
        None: The function processes the unit arguments and displays the conversion table.
    """
    unit = str(unit_args[0] if len(unit_args) >= 1 else "s")
    columns = int(unit_args[1]) if len(unit_args) >= 2 else 5
    rows = int(unit_args[2]) if len(unit_args) >= 3 else 100
    config.units.print_conversion_table(unit, columns, rows)


def handle_conversion_args(conv_args: List[Union[str, Decimal]]) -> None:
    """
    Handles the `--conv` argument for unit conversions.

    Args:
        conv_args (list): The list of arguments for the `--conv` flag.

    Returns:
        None: The function performs the unit conversion based on the provided arguments.
    """
    value = Decimal(conv_args[0])
    source_unit = str(conv_args[1])
    target_unit = str(conv_args[2]) if len(conv_args) == 3 else None
    config.units.convert_units(value, source_unit, target_unit)


def handle_dconv_args(dconv_args: List[str]) -> None:
    """
    Handles the `--dconv` argument for day-time conversions.

    Args:
        dconv_args (list): The list of arguments for the `--dconv` flag.

    Returns:
        None: The function converts the day-time value based on the provided argument.
    """
    value = dconv_args[0]
    print(convert_time(value))


def handle_config_args(config_args: List[str]) -> None:
    """
    Handles the `--config` argument for UTMS configuration.

    Args:
        config_args (list): The list of arguments for the `--config` flag.

    Returns:
        None: The function configures UTMS.
    """
    if not config_args:
        config.print_values()
        return
    if config_args[0] == "set":
        if len(config_args) == 1:
            print_error("At least a key should be specified with `config set <key> [value]`")
            return
        if len(config_args) == 2:
            config.select_from_choices(config_args[1])
            return
        config.set_value(config_args[1], config_args[2])
    else:
        config.print_values(config_args[0])
        return
