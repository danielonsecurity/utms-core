"""
Module for managing command hierarchy and handling in the UTMS CLI system.

This module defines the `CommandHierarchy` class, which is responsible for organizing
commands and subcommands, managing their argument parsers, handling associated functions,
and establishing default behaviors for commands. It allows the UTMS CLI system to parse
and execute commands and subcommands effectively.

Imports:
    - `argparse`: Standard library for command-line argument parsing.
    - `Any`, `Callable`, `Dict`, `Optional`: Typing annotations for type hints.

Exports:
    - `CommandHierarchy`: Class that handles the management of commands, subcommands,
      parsers, and handlers in the CLI system.

Usage:
    The `CommandHierarchy` class is used to define the structure and behavior of commands
    and subcommands in the UTMS CLI, including associating them with specific parsers and handlers.
"""

import argparse
from typing import Any, Callable, Dict, Optional


class CommandHierarchy:
    """
    Manages the hierarchy of commands and subcommands for the UTMS CLI system.

    The `CommandHierarchy` class is responsible for organizing commands and their subcommands,
    associating them with argument parsers, and mapping them to their respective handler functions.
    It also allows for the definition of default subcommands for specific commands.

    Attributes:
        parent_parsers (Dict[str, argparse.ArgumentParser]): A
        dictionary mapping top-level commands to their parsers.
        child_parsers (Dict[str, Dict[str, argparse.ArgumentParser]]):
        A dictionary mapping commands to their subcommand parsers.
        subparsers_actions (Dict[str,
        argparse._SubParsersAction[Any]]): A dictionary storing
        subparsers actions for commands.
        default_subcommands (Dict[str, str]): A dictionary mapping
        commands to their default subcommands.
        handlers (Dict[str, Dict[Optional[str],
        Callable[[argparse.Namespace], None]]]): A dictionary mapping
        commands and subcommands to their handler functions.

    Methods:
        __init__() -> None:
            Initializes the command hierarchy.
        add_parent_parser(command: str, parser: argparse.ArgumentParser) -> None:
            Adds a top-level command and its corresponding parser.
        add_subcommand(command: str, subcommand: str, parser:
            argparse.ArgumentParser) -> None: Adds a subcommand and
            its associated parser.
        add_handler(handler: Callable[[argparse.Namespace], None],
        command: str, subcommand: Optional[str] = None) -> None:
            Adds a handler function for a command or subcommand.
        add_subparsers_actions(command: str, actions: argparse._SubParsersAction[Any]) -> None:
            Adds subparser actions for a command.
        set_default_subcommand(command: str, subcommand: str) -> None:
            Sets the default subcommand for a given command.
        get_handler(command: Optional[str], subcommand: Optional[str]
        = None) -> Optional[Callable[[argparse.Namespace], None]]:
            Retrieves the handler function for a command or subcommand.
        get_parser(command: str, subcommand: Optional[str] = None) ->
        Optional[argparse.ArgumentParser]:
            Retrieves the parser for a given command and subcommand.
        get_action(command: str) -> argparse._SubParsersAction[Any]:
            Retrieves the subparser action for a command.
        root_actions() -> argparse._SubParsersAction[Any]:
            Property that retrieves the root subparser actions for the CLI.
    """

    def __init__(self) -> None:
        """
        Initializes the command hierarchy, setting up containers for parent parsers,
        child parsers, subparser actions, default subcommands, and handler functions.

        This constructor sets up empty dictionaries for organizing and storing
        command-related data that will be populated through various methods.

        Args:
            None
        """
        self.parent_parsers: Dict[str, argparse.ArgumentParser] = {}
        self.child_parsers: Dict[str, Dict[str, argparse.ArgumentParser]] = {}
        self.subparsers_actions: Dict[str, "argparse._SubParsersAction[Any]"] = {}
        self.default_subcommands: Dict[str, str] = {}
        self.handlers: Dict[str, Dict[Optional[str], Callable[[argparse.Namespace], None]]] = {}

    def add_parent_parser(self, command: str, parser: argparse.ArgumentParser) -> None:
        """
        Adds a top-level command and its corresponding parser to the hierarchy.

        This method stores the parser for a top-level command (parent command)
        in the `parent_parsers` dictionary for later use.

        Args:
            command (str): The name of the command (e.g., 'config', 'anchor').
            parser (argparse.ArgumentParser): The parser for the command.
        """
        self.parent_parsers[command] = parser

    def add_subcommand(
        self, command: str, subcommand: str, parser: argparse.ArgumentParser
    ) -> None:
        """
        Adds a subcommand and its associated parser to the hierarchy.

        This method stores the parser for a subcommand under the relevant command
        in the `child_parsers` dictionary for later use.

        Args:
            command (str): The name of the parent command (e.g., 'config').
            subcommand (str): The name of the subcommand (e.g., 'get').
            parser (argparse.ArgumentParser): The parser for the subcommand.
        """
        if command not in self.child_parsers:
            self.child_parsers[command] = {}
        self.child_parsers[command][subcommand] = parser

    def add_handler(
        self,
        handler: Callable[[argparse.Namespace], None],
        command: str,
        subcommand: Optional[str] = None,
    ) -> None:
        """
        Adds a handler function for a command or subcommand.

        This method stores the handler function for a given command and, if applicable,
        its subcommand, in the `handlers` dictionary.

        Args:
            handler (Callable[[argparse.Namespace], None]): The
            function that handles the command or subcommand.
            command (str): The name of the command (e.g., 'config').
            subcommand (Optional[str]): The name of the subcommand
            (e.g., 'get'). If None, it is for the parent command.
        """
        if command not in self.handlers:
            self.handlers[command] = {}
        self.handlers[command][subcommand] = handler

    def add_subparsers_actions(
        self, command: str, actions: "argparse._SubParsersAction[Any]"
    ) -> None:
        """
        Adds subparser actions for a command.

        This method associates a command with its subparser actions, enabling the command
        to have subcommands that can be handled properly.

        Args:
            command (str): The name of the command.
            actions (argparse._SubParsersAction[Any]): The subparser
            actions to add for the command.
        """
        self.subparsers_actions[command] = actions

    def set_default_subcommand(self, command: str, subcommand: str) -> None:
        """
        Sets the default subcommand for a given command.

        This method allows for specifying a default subcommand that should be invoked
        if no subcommand is provided when invoking a command.

        Args:
            command (str): The name of the command (e.g., 'config').
            subcommand (str): The name of the default subcommand (e.g., 'list').
        """
        self.default_subcommands[command] = subcommand

    def get_handler(
        self, command: Optional[str], subcommand: Optional[str] = None
    ) -> Optional[Callable[[argparse.Namespace], None]]:
        """
        Retrieves the handler function for a command or subcommand.

        This method looks up the appropriate handler function based on the provided
        command and, if applicable, subcommand.

        Args:
            command (Optional[str]): The name of the command (e.g., 'config').
            subcommand (Optional[str]): The name of the subcommand
            (e.g., 'get'). If None, it will fetch the handler for the
            command itself.

        Returns:
            Optional[Callable[[argparse.Namespace], None]]: The
            handler function, or None if not found.
        """
        if command:
            return self.handlers[command][subcommand]
        return None

    def get_parser(
        self, command: str, subcommand: Optional[str] = None
    ) -> Optional[argparse.ArgumentParser]:
        """
        Retrieves the parser for a given command and subcommand.

        This method looks up the parser for the specified command and subcommand. If
        no subcommand is given, the method returns the parser for the command itself.

        Args:
            command (str): The name of the command (e.g., 'config').
            subcommand (Optional[str]): The name of the subcommand
            (e.g., 'get'). If None, the command's parser is returned.

        Returns:
            Optional[argparse.ArgumentParser]: The associated argument
            parser, or None if not found.
        """
        if command in self.parent_parsers:
            if subcommand is None:
                # Return the top-level parser if no subcommand is given
                return self.parent_parsers[command]
            if subcommand in self.child_parsers.get(command, {}):
                # Return the subcommand parser if it exists
                return self.child_parsers[command][subcommand]
        return None

    def get_action(self, command: str) -> "argparse._SubParsersAction[Any]":
        """
        Retrieves the subparser action for a command.

        This method returns the subparser action object that manages the subcommands for
        the specified command.

        Args:
            command (str): The name of the command.

        Returns:
            argparse._SubParsersAction[Any]: The subparser action associated with the command.
        """
        return self.subparsers_actions[command]

    @property
    def root_actions(self) -> "argparse._SubParsersAction[Any]":
        """
        Retrieves the root subparser actions for the CLI.

        This property returns the subparser action for the root command, which is used
        to manage top-level commands and subcommands.

        Returns:
            argparse._SubParsersAction[Any]: The root subparser action for the CLI.
        """
        return self.subparsers_actions["__root__"]
