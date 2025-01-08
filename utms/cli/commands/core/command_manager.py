"""
Module for managing and processing commands in the UTMS CLI.

This module defines the `CommandManager` class, which is responsible for registering,
configuring, and processing commands in the UTMS CLI. It allows the definition of commands
and subcommands, with handlers for executing the desired functionality. It also handles
argument parsing and interaction via the `argparse` module, enabling both interactive
and non-interactive command executions.

Imports:
    - `argparse`: Standard library for argument parsing.
    - `pdb`: Python debugger, used for debugging execution.
    - `shlex`: Used to split input text into arguments.
    - `Dict`, `Optional`: Typing annotations for type hints.
    - `Config`: Configuration object used in the CLI.
    - `Command`: The `Command` class for defining CLI commands.
    - `CommandHierarchy`: A class to manage the hierarchy and subcommands.

Exports:
    - `CommandManager`: Class for managing and processing commands.
"""

import argparse
import pdb
import shlex
from typing import Dict, Optional

from utms import VERSION, Config
from utms.cli.commands.core.command import Command
from utms.cli.commands.core.hierarchy import CommandHierarchy


class CommandManager:
    """
    A class responsible for managing and processing commands in the UTMS CLI.

    The `CommandManager` class handles registering commands, configuring their parsers,
    and processing command-line arguments. It supports both root commands and subcommands,
    and can execute the associated handler based on parsed arguments.

    Attributes:
        config (Config): The configuration object.
        parser (argparse.ArgumentParser): Argument parser instance for CLI commands.
        commands (Dict[str, Dict[Optional[str], Command]]): A dictionary of commands and
            their associated subcommands.
        hierarchy (CommandHierarchy): Manages the hierarchy and structure of commands.

    Methods:
        register_command(cmd: Command) -> None:
            Registers a command and its associated handler.
        add_subparser(command: str, subcommands: Optional[bool] = True) -> argparse.ArgumentParser:
            Adds a subparser for a command or subcommand.
        configure_parsers() -> None:
            Configures argument parsers for all registered commands.
        process_args(input_text: Optional[list[str]] = None) -> bool:
            Processes command-line arguments and executes the associated handler.
        handle(input_text: str) -> bool:
            Handles input, processes arguments, and returns the result.
    """

    def __init__(self, config: Config) -> None:
        self.config = config
        self.parser = argparse.ArgumentParser(description=f"UTMS CLI version {VERSION}")
        root_subparser_actions = self.parser.add_subparsers(dest="command", help="Main commands")
        self.commands: Dict[str, Dict[Optional[str], Command]] = {}

        self.hierarchy = CommandHierarchy()
        self.hierarchy.add_subparsers_actions("__root__", root_subparser_actions)

    def register_command(
        self,
        cmd: Command,
    ) -> None:
        """
        Registers a command and its associated handler.

        This method registers a command with the `CommandManager` instance, along with
        its associated handler, subcommand (if any), and adds it to the command hierarchy.

        Args:
            cmd (Command): The command to register.
        """
        if cmd.command not in self.commands:
            self.commands[cmd.command] = {}

        subcommand = cmd.subcommand or None  # Explicitly handle no subcommand
        self.commands[cmd.command][subcommand] = cmd

        self.hierarchy.add_handler(cmd.handler, cmd.command, cmd.subcommand)

    def add_subparser(
        self, command: str, subcommands: Optional[bool] = True
    ) -> argparse.ArgumentParser:
        """
        Adds a subparser for the command to the main parser or a parent command.

        This method configures a subparser for the specified command. It also optionally
        supports subcommands, adding them to the command parser if specified.

        Args:
            command (str): The command to add a subparser for.
            subcommands (Optional[bool]): Whether the command should
            support subcommands. Defaults to True.

        Returns:
            argparse.ArgumentParser: The subparser instance for the command.
        """
        command_parser: argparse.ArgumentParser
        root_subparser = self.hierarchy.root_actions
        command_parser = root_subparser.add_parser(
            command, help=f"{command} management", formatter_class=argparse.RawTextHelpFormatter
        )
        self.hierarchy.add_parent_parser(command, command_parser)

        if subcommands:
            if command not in self.hierarchy.subparsers_actions:
                command_subparsers = command_parser.add_subparsers(
                    dest="subcommand", help=f"{command} subcommands"
                )
                self.hierarchy.add_subparsers_actions(command, command_subparsers)

        return command_parser

    def configure_parsers(self) -> None:
        """
        Configures the parsers for each command and adds their arguments.

        This method is called after all commands are registered to set up argument parsing
        for each command and subcommand. It ensures that each command has a parser with
        the appropriate arguments.

        This is essential to ensure that arguments are correctly parsed and mapped
        to their respective handlers.
        """
        for command_group in self.commands.values():
            for cmd in command_group.values():
                # Check if the command has subcommands
                if cmd.subcommand is None:
                    # If no subcommand is expected, add the command's arguments directly
                    command_parser = self.add_subparser(cmd.command, False)
                    if hasattr(cmd, "configure_parser"):
                        cmd.configure_parser(command_parser)
                else:
                    # Add or reuse the parent command parser for subcommands
                    if cmd.command not in self.hierarchy.parent_parsers:
                        command_parser = self.add_subparser(cmd.command)

                    # Add the subcommand to the subparsers
                    subparsers_action = self.hierarchy.get_action(cmd.command)

                    if subparsers_action is not None:
                        subcommand_parser = subparsers_action.add_parser(
                            cmd.subcommand,
                            help=cmd.help,
                            formatter_class=argparse.RawTextHelpFormatter,
                        )
                        self.hierarchy.add_subcommand(
                            cmd.command, cmd.subcommand, subcommand_parser
                        )
                        # Add subcommand-specific arguments
                        if hasattr(cmd, "configure_parser"):
                            cmd.configure_parser(subcommand_parser)

                        if cmd.is_default:
                            self.hierarchy.parent_parsers[cmd.command].set_defaults(
                                subcommand=cmd.subcommand
                            )
                            self.hierarchy.set_default_subcommand(cmd.command, cmd.subcommand)

    def process_args(self, input_text: Optional[list[str]] = None) -> bool:
        """
        Processes non-interactive execution based on command-line arguments.

        This method parses the provided input text (if any) and resolves the correct command
        and subcommand. It then invokes the handler associated with the resolved command.

        Args:
            input_text (Optional[list[str]]): The command-line arguments to process. If None,
                defaults to using `sys.argv`.

        Returns:
            bool: `True` if an argument was processed successfully, `False` otherwise.
        """
        args = self.parser.parse_args(input_text)
        if hasattr(args, "subcommand"):
            subcommand = args.subcommand
        else:
            subcommand = None
        handler = self.hierarchy.get_handler(args.command, subcommand)

        if args.version:
            print(VERSION)
            return True
        if args.debug:
            pdb.set_trace()  # pylint: disable=forgotten-debug-statement
            return True
        if handler:
            handler(args)
            return True
        if args.command:
            print(f"Unknown subcommand: {args.subcommand} for command: {args.command}")
        else:
            print("Unknown command.")
        return False

    def handle(self, input_text: str) -> bool:
        """
        Handles the input and processes the associated command.

        This method processes a command string by splitting it into arguments and then
        handling the execution based on parsed arguments.

        Args:
            input_text (str): The raw input text (command string) to handle.

        Returns:
            bool: `True` if the command was processed successfully, `False` otherwise.
        """
        try:
            return self.process_args(shlex.split(input_text))
        except SystemExit:
            # Handle argparse exiting on bad input
            print(f"Invalid input: {input_text}. Use '.help' for available commands.")
            return False
