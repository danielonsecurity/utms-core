"""
This module implements a Command Line Interface (CLI) for the
Universal Time Measurement System (UTMS).  It allows users to
interactively input commands for time and date-related conversions,
resolving and displaying formatted timestamps based on their input.

**Key Features**:
1. **Interactive Shell**: Provides a command-line interface with input
   handling, autocompletion, and a stylish prompt for user commands.
2. **Command Handling**: The CLI supports specific commands like
   `.conv` for various conversion tables and dynamic date resolution.
3. **Date/Time Resolution**: The input can be processed to resolve
   specific dates or timestamps, including handling special terms like
   "yesterday", "tomorrow", or "now".
4. **Error Handling**: Gracefully handles invalid inputs and
   interruptions, providing helpful error messages to the user.

**Dependencies**:
- `prompt_toolkit`: A library for building interactive CLI
  applications, enabling features like autocompletion and input
  history.
- `utms.constants`: Includes version information and manager for
  conversion functionality.
- `utms.utils`: Contains utility functions like
   `print_time`, and
  `resolve_date`.

**Usage Example**:
```python
>>> main()
Welcome to UTMS CLI (Version 1.0.0)!
Current time: 2024-12-14T20:00:00+00:00
Prompt> .conv concise
"""

import argparse
import pdb
import re
import sys
import threading
from datetime import datetime
from decimal import Decimal
from typing import List, Union

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.shortcuts import print_formatted_text
from prompt_toolkit.styles import Style

from utms import VERSION
from utms.clock import run_clock
from utms.config import Config
from utms.utils import convert_time, generate_time_table, print_time, resolve_date

config = Config()

# Create a style for the shell
style = Style.from_dict({"prompt": "#ff6600 bold", "input": "#008800", "output": "#00ff00"})

# Define a simple WordCompleter (autocompletion for date formats, or any other completions)
completer = WordCompleter(
    [
        "yesterday",
        "tomorrow",
        "today",
        "now",
        "exit",
        ".clock",
        ".conv",
        ".dconv",
        ".debug",
        ".help",
        ".timetable",
        ".unit",
    ],
    ignore_case=True,
    pattern=re.compile(
        r"[^ ]+"
    ),  # Custom pattern: Match sequences of non-space characters (so dot commands will work)
)

# History for command input
history = InMemoryHistory()

# Create the interactive session
session: PromptSession[str] = PromptSession(completer=completer, history=history, style=style)

HELP_MESSAGE = """
Input the date you want to check. If not a standard date format, AI will be used to convert your
text into a parseable date. If your input starts with a dot (`.`) it'll be interpreted as a command.

Available Commands:

.unit [unit] [columns] [rows]
    Display a conversion table for a specific unit. The parameters are optional:
    - [unit]: The base unit for the conversion table ("s", "m", etc)
      Defaults to "s" if omitted.
    - [columns]: Number of columns before and after the base unit in
      the table. Defaults to a standard layout if omitted.
    - [rows]: Number of rows before and after the base unit in
      the table. Defaults to a standard layout if omitted.
    Examples:
        .unit s
        .unit m 5
        .unit h 3 10

.conv <value> <source_unit> [target_unit]
    Convert a value from one unit to another. The `target_unit` is optional:
    - <value>: The numerical value to be converted.
    - <source_unit>: The unit of the value to be converted.
    - [target_unit]: The desired unit to convert to. If omitted,
      defaults to a standard unit conversion.
    Examples:
        .conv 60 s m
        .conv 1 h

.dconv <value>
    Convert a date time value from one unit to another.
    - <value>: The date time value to be converted in either HH:MM[:SS] or DD.CC[.SSS] format
    Examples:
        .conv 10:05
        .conv 17:35:33
        .conv 3.2.250
        .conv 8.9

.timetable
    Prints a formated table mapping standard hours/minutes to centidays/decidays and also
    Kiloseconds

General:
    .exit
        Exit the UTMS CLI.
    .debug
        Enter Python's PDB.
    .clock
        Run a clock showing time both in standard units and new ones.
    .help
        Display this help message.

Notes:
- Commands are case-sensitive and must begin with a period (`.`).
"""


def handle_input(input_text: str) -> None:
    """
    Processes the input text to execute a corresponding command based on the provided input.

    This function handles commands starting with `.unit` and `.conv`. Each command has
    its own handler for arguments.

    Args:
        input_text (str): The input string, typically a command prefixed with `.unit` or `.conv`.

    Returns:
        None: The function performs actions based on the input and does not return any value.
    """
    if input_text.startswith(".unit"):
        handle_unit_command(input_text)
    elif input_text.startswith(".conv"):
        handle_conversion_command(input_text)


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


def handle_conversion_command(input_text: str) -> None:
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


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns
    -------
    Namespace
        An argparse.Namespace object containing the parsed arguments.
    """
    parser = argparse.ArgumentParser(description="UTMS CLI")
    parser.add_argument("--unit", nargs="*", help="Unit conversion table")
    parser.add_argument("--conv", nargs="+", help="Convert value between units")
    parser.add_argument("--dconv", nargs="+", help="Convert day time between units")
    parser.add_argument("--timetable", action="store_true", help="Generate timetable")
    parser.add_argument("--clock", action="store_true", help="Run clock")
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
    if args.unit:
        handle_unit_args(args.unit)
    elif args.conv:
        handle_conversion_args(args.conv)
    elif args.dconv:
        handle_dconv_args(args.dconv)
    elif args.timetable:
        print(generate_time_table())
    elif args.clock:
        run_clock()
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


def handle_command(input_text: str) -> bool:
    """
    Handle different commands based on user input.

    This function maps each command (such as `.help`, `.clock`, etc.) to specific handler
    functions. It returns `True` if the command is recognized and handled, or `False` if
    the command is unknown.

    Args:
        input_text (str): The user command input.

    Returns:
        bool: True if the command was handled, False otherwise.
    """
    command_map = {
        "exit": exit_shell,
        ".help": show_help,
        ".debug": start_debugging,
        ".clock": start_clock,
        ".timetable": show_timetable,
    }

    # Check for known commands
    if input_text.lower() in command_map:
        command_map[input_text.lower()](input_text)
        return True
    if input_text.startswith("."):
        handle_input(input_text)
        return True
    # Resolve date or other input logic
    parsed_timestamp = resolve_date(input_text)
    if isinstance(parsed_timestamp, (datetime, Decimal)):
        print_time(parsed_timestamp, config)
        return True
    return False


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


def show_help(_: str) -> None:
    """
    Displays the help message when the '.help' command is invoked.

    Args:
        input_text (str): The user input. This parameter is not used in this function.

    Returns:
        None: The function prints the help message to the screen.
    """
    print(HELP_MESSAGE)


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


def main() -> None:
    """
    Main entry point for the UTMS CLI (Universal Time Measurement System Command Line Interface).

    This function starts an interactive shell where the user can enter commands, including
    options for unit conversion, time resolution, and more. The loop continues until the user
    decides to exit.

    Args:
        None: This function does not take any arguments.

    Returns:
        None: The function runs interactively and performs actions based on user input.
    """
    args = parse_args()
    if process_args(args):
        return

    print(f"Welcome to UTMS CLI (Version {VERSION})!")
    print(HELP_MESSAGE)

    while True:
        try:
            input_text = session.prompt("UTMS> ").strip()

            if not input_text:
                continue

            # Handle commands using a dictionary map
            if not handle_command(input_text):
                print(f"Unknown command: {input_text}")

        except (ValueError, KeyboardInterrupt) as e:
            print_error(str(e))
        except EOFError:
            print("\nExiting gracefully. Goodbye!")
            return
