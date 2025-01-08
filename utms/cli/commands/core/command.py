"""
Module for defining the Command class used for CLI command management.

This module contains the `Command` class, which is used to represent a command in the
UTMS CLI system. The class encapsulates the command name, subcommand (if any), handler
function, and associated arguments. It also provides methods to set help and description
text, add arguments, and configure argument parsers for each command.

Imports:
    - `argparse`: Standard library for command-line argument parsing.
    - `Any`, `Callable`, `Dict`, `List`, `Optional`, `Tuple`: Typing annotations for
      type hints.

Exports:
    - `Command`: Class for defining and managing CLI commands.

Usage:
    The `Command` class can be used to define a command, specify its handler, and register
    it with the `CommandManager` for processing user input in the CLI.
"""

import argparse
from typing import Any, Callable, Dict, List, Optional, Tuple


class Command:
    """
    Represents a command in the UTMS CLI system.

    The `Command` class is used to define a command in the CLI, including its name,
    optional subcommand, handler function, arguments, and related metadata (help text,
    description). It also provides methods for configuring the argument parser.

    Attributes:
        command (str): The name of the command (e.g., 'config', 'anchor').
        subcommand (Optional[str]): The name of the subcommand (e.g., 'get', 'set') or None
            if there is no subcommand.
        handler (Callable[[argparse.Namespace], None]): The function to handle the command.
        help (str): The help text for the command.
        description (str): The description text for the command.
        arguments (List[Tuple[Tuple[str, ...], Dict[str, Any]]]): The list of arguments
            for the command.
        is_default (bool): Whether this command is the default action for its category.

    Methods:
        __init__(command: str, subcommand: Optional[str], handler:
        Callable[[argparse.Namespace], None], is_default: bool =
        False) -> None:
            Initializes a new command with the given properties.
        set_help(help_text: str) -> None:
            Sets the help text for the command.
        set_description(description: str) -> None:
            Sets the description text for the command.
        add_argument(*args: str, **kwargs: Any) -> None:
            Adds an argument to the command.
        configure_parser(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
            Configures the argument parser with the command's arguments and metadata.
    """

    def __init__(
        self,
        command: str,
        subcommand: Optional[str],
        handler: Callable[[argparse.Namespace], None],
        is_default: bool = False,
    ) -> None:
        """
        Initializes a new command with the given properties.

        Args:
            command (str): The name of the command (e.g., 'config', 'anchor').
            subcommand (Optional[str]): The subcommand (e.g., 'get', 'set') or None if there
                is no subcommand.
            handler (Callable[[argparse.Namespace], None]): The function to handle the command.
            is_default (bool): Whether this command is the default for
            its category (default is False).
        """
        self.command = command
        self.subcommand = subcommand
        self.handler = handler
        self.help = ""
        self.description = ""
        self.arguments: List[Tuple[Tuple[str, ...], Dict[str, Any]]] = []
        self.is_default = is_default

    def set_help(self, help_text: str) -> None:
        """
        Sets the help text for the command.

        This text is displayed when the user requests help for the command in the CLI.

        Args:
            help_text (str): The help text to be displayed for the command.
        """
        self.help = help_text

    def set_description(self, description: str) -> None:
        """
        Sets the description text for the command.

        This description provides further information about the command's purpose
        and behavior, typically shown in the CLI help output.

        Args:
            description (str): The description to be displayed for the command.
        """
        self.description = description

    def add_argument(self, *args: str, **kwargs: Any) -> None:
        """
        Adds an argument to the command.

        This method allows defining the command-line arguments for the command,
        such as required flags or values.

        Args:
            *args (str): The argument(s) to be added to the command (e.g., 'key', '--verbose').
            **kwargs (Any): Additional keyword arguments for the argument configuration
                (e.g., type, help).
        """
        self.arguments.append((args, kwargs))

    def configure_parser(self, parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
        """
        Configures the argument parser with the command's arguments and metadata.

        This method iterates over the command's arguments and adds them to the provided
        argument parser. It also sets the help and description text for the command.

        Args:
            parser (argparse.ArgumentParser): The argument parser to configure.

        Returns:
            argparse.ArgumentParser: The updated argument parser with the command's
                arguments and metadata.
        """
        # Add command-specific arguments
        for args, kwargs in self.arguments:
            parser.add_argument(*args, **kwargs)

        # Set help and description if available
        if self.help:
            parser.description = self.help
        if self.description:
            if parser.description:
                parser.description += f"\n\n{self.description}"
            else:
                parser.description = f"\n\n{self.description}"

        return parser
