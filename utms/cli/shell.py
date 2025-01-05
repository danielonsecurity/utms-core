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

import re

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style

from utms.cli.args import parse_args, process_args
from utms.cli.commands import CommandManager, load_default_commands
from utms.cli.helpers import exit_shell
from utms.config import Config

config = Config()

# Create a style for the shell
style = Style.from_dict({"prompt": "#ff6600 bold", "input": "#008800", "output": "#00ff00"})


def interactive_shell(command_manager: CommandManager) -> None:
    """
    Starts an interactive command-line shell for the UTMS CLI.

    This function enters a loop where it prompts the user for input, processes the input to invoke
    the corresponding command, and displays the output. The user can exit the shell by typing
    `exit`.

    Args:
        command_manager (CommandManager): The manager responsible for handling and executing
        commands.

    Returns:
        None: This function runs in an infinite loop until the user exits the shell.
    """
    print("Welcome to UTMS CLI!")
    print(command_manager.generate_help_message())

    completer = WordCompleter(
        list(command_manager.commands.keys()), ignore_case=True, pattern=re.compile(r"[^ ]+")
    )
    session = PromptSession(completer=completer, style=style)

    while True:
        try:
            input_text = session.prompt("UTMS> ").strip()
            if input_text:
                command_manager.handle(input_text)
        except EOFError:
            exit_shell("")
        except KeyboardInterrupt:
            pass


def main() -> None:
    """
    Main entry point of the UTMS CLI application.

    This function parses command-line arguments and starts the interactive shell if no immediate
    action (like argument processing) is required.

    Args:
        None: This function retrieves and processes command-line arguments, then initializes the
        CLI.

    Returns:
        None: The function either starts the interactive shell or terminates if arguments are
        processed.
    """
    args = parse_args()
    if process_args(args):
        return

    command_manager = CommandManager()
    load_default_commands(command_manager)
    interactive_shell(command_manager)
