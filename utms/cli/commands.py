"""
UTMS Command Manager Module

This module defines a command registry and manager system for the UTMS (Universal Time Management
System) command-line interface (CLI). It provides functionality for registering, handling, and
executing user commands. Each command is associated with a unique name, an optional help message, a
handler function, and optional arguments.

Commands in the UTMS CLI include functionalities such as:
- Displaying help messages (`.help`).
- Exiting the CLI (`.exit`).
- Entering Python's debugger (`.debug`).
- Running a clock to show time in various units (`.clock`).
- Displaying a formatted timetable (`.timetable`).
- Handling unit conversions (`.unit`).
- Converting between units (`.conv`).
- Configuring UTMS settings (`.config`).
- Converting date-time values (`.dconv`).

Classes
--------
- `Command`: Represents a command in the command registry. Each command consists of:
    - `name`: The command identifier (e.g., `.help`).
    - `help_message`: A description of the command's functionality.
    - `handler`: A function to execute when the command is invoked.
    - `args`: Optional arguments for the command.

- `CommandManager`: Manages the command registry, handling registration, execution, and help message
  generation for commands.
    - `register(command: Command)`: Registers a command in the manager.
    - `handle(input_text: str)`: Processes the input and invokes the appropriate handler.
    - `generate_help_message()`: Generates and returns a formatted help message listing all
      available commands.

Functions
---------
- `load_default_commands(manager: CommandManager)`: Loads the default set of commands into the
  provided `CommandManager`.
- `handle_command(input_text: str)`: Processes the input command and executes the corresponding
  handler. Returns `True` if the command is recognized, `False` otherwise.

Constants
---------
- `HELP_MESSAGE_*`: Constants defining help messages for various commands.

Modules Imported
----------------
- `dataclasses`: For defining the `Command` class with `@dataclass`.
- `datetime`: For working with date-time values.
- `decimal.Decimal`: For handling high-precision decimal values.
- `typing`: For type annotations, including `Callable`, `Dict`, `List`, `Optional`, and `Union`.
- `utms.cli.helpers`: For importing command handler functions.
- `utms.config.Config`: For managing UTMS configuration.
- `utms.utils`: For utility functions like printing time and resolving date values.

Usage Example
-------------
To handle a command and invoke its handler:
    >>> command_manager = CommandManager()
    >>> load_default_commands(command_manager)
    >>> command_manager.handle(".help")  # Prints available commands help message.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Callable, Dict, Optional

from utms.cli.helpers import (
    exit_shell,
    handle_config_command,
    handle_conv_command,
    handle_dconv_command,
    handle_unit_command,
    show_timetable,
    start_clock,
    start_debugging,
)
from utms.config import Config
from utms.utils import print_time, resolve_date

config = Config()

HELP_MESSAGE_HELP = """
Display this help message.
"""

HELP_MESSAGE_EXIT = """
Exit the UTMS CLI.
"""

HELP_MESSAGE_DEBUG = """
Enter Python's PDB.
"""

HELP_MESSAGE_CLOCK = """
Run a clock showing time both in standard units and new ones.
"""

HELP_MESSAGE_TIMETABLE = """
Prints a formatted table mapping standard hours/minutes to centidays/decidays and also
Kiloseconds.
"""

HELP_MESSAGE_UNIT = """
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
"""

HELP_MESSAGE_CONV = """
Convert a value from one unit to another. The `target_unit` is optional:
- <value>: The numerical value to be converted.
- <source_unit>: The unit of the value to be converted.
- [target_unit]: The desired unit to convert to. If omitted,
  defaults to a standard unit conversion.
Examples:
    .conv 60 s m
    .conv 1 h
"""

HELP_MESSAGE_CONFIG = """
Get or [set] UTMS configuration options.
Examples:
    .config
    .config gemini.api_key
    .config set gemini_api_key
    .config set gemini_api_key ABCDE
"""

HELP_MESSAGE_DCONV = """
Convert a date time value from one unit to another.
- <value>: The date time value to be converted in either HH:MM[:SS] or DD.CC[.SSS] format.
Examples:
    .conv 10:05
    .conv 17:35:33
    .conv 3.2.250
    .conv 8.9
"""


@dataclass
class Command:
    """
    Represents a command in a command registry system.

    Each command consists of a name, an optional help message, a handler function
    to execute when the command is invoked, and optional arguments.

    Attributes:
        name (str): The unique identifier for the command (e.g., '.help').
        help_message (str): A brief description of what the command does.
        handler (Callable[[str], None]): A function to handle the command's logic.
            The handler is expected to take a single string argument (e.g., user input).
        args (Optional[str]): Additional arguments required for the command.
            Defaults to None if no arguments are needed.

    Example:
        >>> def handle_hello(args: str) -> None:
        ...     print(f"Hello, {args}!")
        ...
        >>> cmd = Command(
        ...     name=".hello",
        ...     help_message="Greets the user.",
        ...     handler=handle_hello,
        ...     args="John"
        ... )
        >>> cmd.handler(cmd.args)  # Output: Hello, John!
    """

    name: str
    help_message: str
    handler: Callable[[str], None]
    args: Optional[str] = None


class CommandManager:
    """
    Manages the registration, execution, and help message generation for commands in the UTMS CLI.

    This class provides functionality to register commands, handle user input, and generate help
    messages listing all available commands. Each command can have a unique name, an associated
    handler, and optional arguments.

    Attributes:
        commands (Dict[str, Command]): A dictionary storing the registered commands, where the keys
                                      are command names (e.g., '.help') and the values are `Command`
                                      objects.

    Methods:
        register(command: Command) -> None:
            Registers a `Command` in the command manager.

        handle(input_text: str) -> bool:
            Processes the input text, identifies the corresponding command, and invokes its handler.
            If the input is not recognized as a command, it attempts to resolve the input as a date.

        generate_help_message() -> str:
            Generates a formatted help message listing all available commands, their descriptions,
            and required arguments.
    """

    def __init__(self) -> None:
        """
        Initializes the CommandManager instance with an empty dictionary of commands.

        The dictionary is used to store registered commands where the key is the command name and
        the value is the corresponding `Command` object.
        """
        self.commands: Dict[str, Command] = {}

    def register(self, command: Command) -> None:
        """
        Registers a `Command` in the command manager.

        Args:
            command (Command): The `Command` object to register in the manager.

        This method adds the command to the internal `commands` dictionary, using the command's name
        as the key.
        """
        self.commands[command.name] = command

    def handle(self, input_text: str) -> bool:
        """
        Processes the input text and invokes the corresponding command handler.

        This method checks if the input starts with a dot (`.`), indicating it is a command. It
        looks up the command in the registered commands, and if found, calls the handler
        function. If the command is not recognized, it attempts to resolve the input as a date. If
        successful, it prints the resolved date.

        Args:
            input_text (str): The user input, which may be a command or a date value.

        Returns:
            bool: `True` if the command was recognized and handled, `False` otherwise.
        """
        parts = input_text.split()
        command_name = parts[0]
        if command_name == "exit":
            command = self.commands.get(".exit")
        else:
            command = self.commands.get(command_name)

        if input_text.startswith(".") and not command:
            print(f"Unknown command: {command_name}. Type '.help' for a list of commands.")
            return False

        if command:
            command.handler(input_text)
            return True

        # Fallback: resolve dates
        parsed_timestamp = resolve_date(input_text)
        if isinstance(parsed_timestamp, (datetime, Decimal)):
            print_time(parsed_timestamp, config)
            return True

        return True

    def generate_help_message(self) -> str:
        """
        Generates and returns a formatted help message that lists all available commands with their
        descriptions and arguments.

        This method compiles the names, help messages, and optional arguments for each registered
        command into a formatted string. The result provides the user with an overview of how to use
        each command in the UTMS CLI.

        Returns:
            str: A formatted help message listing all commands and their descriptions.
        """
        help_lines = [
            """
Input the date you want to check. If not a standard date format, AI will be used to convert your
text into a parseable date. If your input starts with a dot (`.`) it'll be interpreted as a
command.\n""",
            "Available Commands:",
        ]
        for cmd in self.commands.values():
            # Format the command name and arguments
            command_line = f"{cmd.name} {cmd.args or ''}"

            # Format the help message with 4 spaces before each line
            formatted_help_message = "\n".join(
                f"    {line}" for line in cmd.help_message.splitlines()
            )

            # Append the command line and the formatted help message
            help_lines.append(f"{command_line}{formatted_help_message}\n")

        help_lines.append(
            """Notes:
  - Commands are case-sensitive and must begin with a period (`.`).
"""
        )

        # Join all the lines and return the result
        return "\n".join(help_lines)


def load_default_commands(manager: CommandManager) -> None:
    """
    Registers the default set of commands with the provided CommandManager.

    This function registers a set of predefined commands in the command manager, each with a
    specific handler function and help message. These commands include basic actions such as
    displaying help, exiting the CLI, starting a clock, and other utility commands related to time
    and unit conversions.

    Args:
        manager (CommandManager): The instance of the `CommandManager` to register the commands
        with.

    The following commands are registered:
        - `.help`: Displays the help message with a list of available commands.
        - `.exit`: Exits the UTMS CLI.
        - `.debug`: Enters Python's debugger.
        - `.clock`: Starts a clock showing time in both standard and new units.
        - `.timetable`: Displays a timetable mapping standard units to other time units.
        - `.unit`: Displays a conversion table for a specified unit.
        - `.conv`: Converts a value from one unit to another.
        - `.config`: Retrieves or sets configuration options for the UTMS CLI.
        - `.dconv`: Converts a date-time value from one format to another.
    """

    def handle_help(_: str) -> None:
        """
        Displays the help message containing information about available commands.

        Args:
            input_text (str): The user input, which is ignored in this case as the help message is
            always generated.
        """
        print(manager.generate_help_message())

    manager.register(Command(".help", HELP_MESSAGE_HELP, handle_help))
    manager.register(Command(".exit", HELP_MESSAGE_EXIT, exit_shell))
    manager.register(Command(".debug", HELP_MESSAGE_DEBUG, start_debugging))
    manager.register(Command(".clock", HELP_MESSAGE_CLOCK, start_clock))
    manager.register(Command(".timetable", HELP_MESSAGE_TIMETABLE, show_timetable))
    manager.register(
        Command(".unit", HELP_MESSAGE_UNIT, handle_unit_command, "[unit] [columns] [rows]")
    )
    manager.register(
        Command(
            ".conv", HELP_MESSAGE_CONV, handle_conv_command, "<value> <source_unit> [target_unit]"
        )
    )
    manager.register(
        Command(".config", HELP_MESSAGE_CONFIG, handle_config_command, "[set] <key> [value]")
    )
    manager.register(Command(".dconv", HELP_MESSAGE_DCONV, handle_dconv_command, "<value>"))
