"""
Command line interface with a prompt is defined here. This file is only dealing with that part.
"""

from datetime import datetime
from typing import Callable, Dict

from prompt_toolkit import ANSI, PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.shortcuts import print_formatted_text
from prompt_toolkit.styles import Style

from uts.constants import VERSION
from uts.utils import (
    get_current_time_ntp,
    print_all_conversions,
    print_concise_conversion_table,
    print_conversion_table,
    print_reversed_conversion_table,
    print_time,
    resolve_date,
)

# Create a style for the shell
style = Style.from_dict({"prompt": "#ff6600 bold", "input": "#008800", "output": "#00ff00"})

# Define a simple WordCompleter (autocompletion for date formats, or any other completions)
completer = WordCompleter(
    ["yesterday", "tomorrow", "today", "now", "exit", ".conv"],
    ignore_case=True,
)

# History for command input
history = InMemoryHistory()

# Create the interactive session
session: PromptSession[str] = PromptSession(completer=completer, history=history, style=style)


def handle_input(input_text: str) -> None:
    """
    Processes the input text to execute a corresponding command based on the provided input.

    This function handles commands that start with `.conv` followed by a subcommand. The supported
    subcommands are:

    - **"concise"**: Calls the `print_concise_conversion_table` function.
    - **"new"**: Calls the `print_conversion_table` function.
    - **"old"**: Calls the `print_reversed_conversion_table` function.
    - **"."**: Calls the `print_all_conversions` function (default action).

    If the input does not match any subcommand, the function defaults to executing
    `print_all_conversions`.

    Args:
        input_text (str): The input string, typically a command prefixed with `.conv`.

    Returns:
        None: The function performs actions based on the input and does not return any value.
    """
    commands: Dict[str, Callable[[], None]] = {
        "concise": print_concise_conversion_table,
        "new": print_conversion_table,
        "old": print_reversed_conversion_table,
        ".": print_all_conversions,
    }

    if input_text.startswith(".conv"):
        # Split the command to check arguments (if any)
        parts = input_text.split()
        if len(parts) == 2:  # .conv <subcommand>
            command = parts[1]
            if command in commands:
                commands[command]()  # Call function mapped to this command
        else:
            # Default .conv behavior (all tables)
            commands["."]()


def main() -> None:
    """
    Main entry point for the UTS CLI (Universal Time System Command Line Interface).

    This function starts an interactive shell where the user can enter commands. The supported
    features include:

    - **Welcome Message**: Displays a message with the version of the CLI.
    - **User Input**: Prompts the user for input using `session.prompt("Prompt> ")`.
    - **Command Handling**:

      - **`.conv <subcommand>`**: Processes conversion commands via `handle_input`.
      - Resolves a date from input text and displays it using `print_time`.

    - **Exit Option**: Allows the user to exit the shell by typing "exit".
    - **Error Handling**: Catches invalid input or keyboard interrupts and gracefully prints
      appropriate error messages.

    The function runs in a loop until the user chooses to exit.

    Args:
        None: This function does not take any arguments.

    Returns:
        None: It operates interactively and performs actions based on user input without
              returning a value.
    """
    print(f"Welcome to UTS CLI (Version {VERSION})!")
    print_time(get_current_time_ntp())
    while True:
        try:
            # Read user input
            input_text = session.prompt("Prompt> ")

            # Exit condition
            if input_text.lower() == "exit":
                print("Exiting shell...")
                break

            if input_text.startswith(".conv"):
                handle_input(input_text)
                continue

            # Resolve date from input text
            parsed_timestamp = resolve_date(input_text)

            # Ensure parsed_timestamp is a datetime before passing it to print_time
            if isinstance(parsed_timestamp, datetime):
                print_time(parsed_timestamp)
            elif isinstance(parsed_timestamp, str):
                # Handle case where it's a string (if applicable, e.g., parse or log)
                print(f"Resolved date (string): {parsed_timestamp}")
            elif isinstance(parsed_timestamp, int):
                # Handle case where it's an integer (if applicable, convert to datetime)
                print(f"Resolved date (integer timestamp): {parsed_timestamp}")

        except ValueError as e:
            # If the input is invalid, print the error message
            print_formatted_text(ANSI(f"[bold red]Error: {str(e)}[/bold red]"))
            continue
        except KeyboardInterrupt:
            continue
