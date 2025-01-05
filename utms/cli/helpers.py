"""
This module provides various utility functions and command handlers for the UTMS CLI.

These functions handle different commands that can be invoked through the command line interface,
such as starting the clock, displaying the timetable, performing unit conversions, and handling
configuration options.  The module also includes functions for handling errors, starting debugging
sessions, and exiting the shell.

The following command handlers are implemented:
- **exit_shell**: Exits the shell.
- **start_debugging**: Starts a Python debugging session using `pdb`.
- **start_clock**: Starts a clock thread showing the time.
- **show_timetable**: Displays a timetable mapping standard units to other time-related systems.
- **handle_unit_command**: Displays conversion tables for specified units.
- **handle_conv_command**: Converts a specified value from one unit to another.
- **handle_dconv_command**: Converts values between decimal and duodecimal systems.
- **handle_config_command**: Retrieves or sets configuration values.
- **print_error**: Prints an error message in red text.

This module integrates with the UTMS configuration and utility functions to manage time, units, and
user interactions efficiently.
"""

import pdb
import sys
import threading
from decimal import Decimal

from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.shortcuts import print_formatted_text
from prompt_toolkit.styles import Style

from utms.clock import run_clock
from utms.config import Config
from utms.utils import convert_time, generate_time_table

config = Config()


def exit_shell(_: str) -> None:
    """
    Exits the shell when the 'exit' command is invoked.

    Args:
        input_text (str): The user input. This parameter is not used in this function.

    Returns:
        None: The function performs an action (exiting the shell) but does not return anything.
    """
    print("Exiting shell...")
    sys.exit()


def start_debugging(_: str) -> None:
    """
    Starts the debugger when the '.debug' command is invoked.

    Args:
        input_text (str): The user input. This parameter is not used in this function.

    Returns:
        None: The function starts a debugging session using `pdb.set_trace()`.
    """
    pdb.set_trace()  # pylint: disable=forgotten-debug-statement


def start_clock(_: str) -> None:
    """
    Starts a new clock thread when the '.clock' command is invoked.

    Args:
        input_text (str): The user input. This parameter is not used in this function.

    Returns:
        None: The function runs the clock in a new thread.
    """
    threading.Thread(target=run_clock, daemon=True).start()


def show_timetable(_: str) -> None:
    """
    Displays the timetable when the '.timetable' command is invoked.

    Args:
        input_text (str): The user input. This parameter is not used in this function.

    Returns:
        None: The function prints the generated timetable.
    """
    print(generate_time_table())


def handle_unit_command(input_text: str) -> None:
    """
    Handles commands related to unit conversion tables, including formatting options.

    Args:
        input_text (str): The input string for the unit command.

    Returns:
        None: The function performs actions based on the unit command.
    """
    parts = input_text.split()
    unit = parts[1] if len(parts) > 1 else "s"
    columns = int(parts[2]) if len(parts) > 2 else 5
    rows = int(parts[3]) if len(parts) > 3 else 100
    config.units.print_conversion_table(unit, columns, rows)


def handle_conv_command(input_text: str) -> None:
    """
    Handles unit conversion commands, processing the value and units specified.

    Args:
        input_text (str): The input string for the conversion command.

    Returns:
        None: The function performs unit conversion and displays the result.
    """
    parts = input_text.split()
    value = Decimal(parts[1])
    source_unit = parts[2]
    target_unit = parts[3] if len(parts) > 3 else None
    config.units.convert_units(value, source_unit, target_unit)


def handle_dconv_command(input_text: str) -> None:
    """
    Handles time conversion commands, converting between decimal to duodecimal systems.

    Args:
        input_text (str): The input string for the conversion command.

    Returns:
        None: The function performs time conversion and displays the result.
    """
    value = input_text.split()[1]
    print(convert_time(value))


def handle_config_command(input_text: str) -> None:
    """
    Handles unit conversion commands, processing the value and units specified.

    Args:
        input_text (str): The input string for the conversion command.

    Returns:
        None: The function performs unit conversion and displays the result.
    """
    parts = input_text.split()
    if len(parts) == 1:
        config.print_values()
    elif len(parts) == 2:
        config.print_values(parts[1])
    elif len(parts) == 3:
        config.set_value(parts[1], parts[2])


def print_error(message: str) -> None:
    """
    Prints an error message in red.

    Args:
        message (str): The error message to display.

    Returns:
        None: The function prints the error message formatted in red text.
    """
    print_formatted_text(
        FormattedText([("class:error", f"Error: {message}")]),
        style=Style.from_dict({"error": "bold fg:red"}),
    )
