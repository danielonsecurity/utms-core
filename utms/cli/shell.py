"""This module implements a Command Line Interface (CLI) for the Universal Time
Measurement System (UTMS).  It allows users to interactively input commands for
time and date-related conversions, resolving and displaying formatted
timestamps based on their input.

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
import sys
from datetime import datetime
from decimal import Decimal
from io import StringIO
from typing import Any, List

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style

from utms import AI, VERSION, Config
from utms.cli.commands.core import CommandManager
from utms.cli.commands.register import register_all_commands
from utms.core.time.utils.formatting import print_time
from utms.core.logger import LoggerManager, get_logger

config = Config()

# Create a style for the shell
style = Style.from_dict({"prompt": "#ff6600 bold", "input": "#008800", "output": "#00ff00"})


def add_global_arguments(command_manager: CommandManager) -> None:
    """Adds global arguments to the main parser managed by CommandManager.

    Args:
        manager: The CommandManager instance.
    """
    command_manager.parser.add_argument("--version", action="store_true", help="Show UTMS version")
    command_manager.parser.add_argument("--debug", action="store_true", help="Enter Python's PDB")
    command_manager.parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                                        help="Set bootstrap logging level")


def print_prompt_help(parser: argparse.ArgumentParser) -> None:
    """Custom print_help to modify the 'usage' line for the prompt help."""
    help_message = StringIO()
    parser.print_help(file=help_message)

    help_message.seek(0)
    help_output = (
        help_message.read()
        .replace("usage: utms ", "UTMS> .")
        .replace("[-h] [--version] [--debug] ", "")
    )

    print(help_output)


def handle_help(input_text: str, command_manager: CommandManager) -> None:
    """Handles the help command in the interactive shell.

    Args:
        input_text (str): The input help command (e.g., '.help unit table').
        parser (argparse.ArgumentParser): The top-level parser.
        subparser_map (Dict[str, argparse.ArgumentParser]): A map of
        registered commands to their parsers.
    """

    if input_text == ".help":
        print_prompt_help(command_manager.parser)
    else:
        clean_input = input_text.split()[1:]  # Remove '.help'
        command = clean_input[0]
        subcommand = clean_input[1] if len(clean_input) > 1 else None
        target_parser = command_manager.hierarchy.get_parser(command, subcommand)
        if target_parser:
            print_prompt_help(target_parser)
        else:
            print(f"No help found for {command} {subcommand}")


def get_word_completer(command_manager: CommandManager) -> WordCompleter:
    """Create a WordCompleter object for both top-level arguments and
    subcommands.

    This function uses the subparser_map from the CommandManager to
    gather the subcommands.
    """

    commands: List[str] = []

    for command in command_manager.hierarchy.parent_parsers.keys():
        commands.append(f".{command}")

    for command, subcommands in command_manager.hierarchy.child_parsers.items():
        commands.append(f".{command}")
        for subcommand in subcommands.keys():
            commands.append(f".{command} {subcommand}")
    commands.extend([f'.help {command.lstrip(".")}' for command in commands])

    commands.extend(["exit", ".exit", ".debug", "now", "today", "tomorrow", "yesterday"])

    commands.sort()

    return WordCompleter(commands, ignore_case=True, sentence=True)


def interactive_shell(command_manager: CommandManager) -> None:
    """Starts an interactive command-line shell for the UTMS CLI.

    This function enters a loop where it prompts the user for input, processes the input to invoke
    the corresponding command, and displays the output. The user can exit the shell by typing
    `exit`.

    Args:
        command_manager (CommandManager): The manager responsible for handling and executing
        commands.

    Returns:
        None: This function runs in an infinite loop until the user exits the shell.
    """
    print(f"Welcome to UTMS CLI! (Version {VERSION})!")
    print(
        """
Input the date you want to check. If not a standard date format, AI will be used to convert your
text into a parseable date. If your input starts with a dot (`.`) it'll be interpreted as a
command.\n"""
    )
    print_prompt_help(command_manager.parser)

    completer = get_word_completer(command_manager)
    session: PromptSession[Any] = PromptSession(completer=completer, style=style)

    while True:
        try:
            input_text = session.prompt("UTMS> ").strip()
            if input_text.startswith(".help"):
                handle_help(input_text, command_manager)
            elif input_text.startswith(".debug"):
                pdb.set_trace()  # pylint: disable=forgotten-debug-statement
            elif input_text in [".exit", "exit"]:
                sys.exit()
            elif input_text.startswith("."):
                command_manager.handle(input_text[1:])
            elif input_text:
                ai = AI(command_manager.config)
                parsed_timestamp = ai.resolve_date(input_text)
                if isinstance(parsed_timestamp, (datetime, Decimal)):
                    print_time(parsed_timestamp, config)
        except EOFError:
            sys.exit()
        except KeyboardInterrupt:
            pass
        except ValueError as e:
            print(e)


def main() -> None:
    """Main entry point of the UTMS CLI application.

    This function parses command-line arguments and starts the interactive shell if no immediate
    action (like argument processing) is required.

    Args:
        None: This function retrieves and processes command-line arguments, then initializes the
        CLI.

    Returns:
        None: The function either starts the interactive shell or terminates if arguments are
        processed.
    """
    LoggerManager.bootstrap()
    bootstrap_logger = get_logger("bootstrap")
    bootstrap_logger.debug("HELP")
    bootstrap_logger.info("INFO")
    bootstrap_logger.warning("WARNING")
    bootstrap_logger.error("ERROR")
    bootstrap_logger.critical("CRITICAL")
    logger = get_logger()
    logger.debug("Starting UTMS CLI")
    logger.debug("Initializing command manager and config")
    command_manager = CommandManager(config)

    logger.debug("Registering commands")
    register_all_commands(command_manager)

    logger.debug("Configuring command parsers")
    command_manager.configure_parsers()

    logger.debug("Adding global arguments")
    add_global_arguments(command_manager)

    if command_manager.process_args():
        logger.debug("Command line arguments processed, exiting")
        return

    logger.info("Starting interactive shell")
    interactive_shell(command_manager)
