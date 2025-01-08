"""
Module for registering and handling the 'resolve' command in the UTMS CLI system.

This module defines the function `register_resolve_command` to
register the 'resolve' command, and `handle_resolve_command` to
process the command by resolving arbitrary strings into dates using
either the `dateparser` library or an AI model. The result is then
printed in a readable time format.

Imports:
    - `argparse`: For handling argument parsing.
    - `datetime`, `Decimal`: For managing date and time-related data types.
    - `AI`, `Config`: For utilizing AI and configuration-related functionality.
    - `Command`, `CommandManager`: For managing the commands in the CLI system.
    - `print_time`: Utility function for printing a formatted time.

Exports:
    - `handle_resolve_command`: Function to handle resolving the input string to a date.
    - `register_resolve_command`: Function to register the resolve command in the CLI.
"""

import argparse
from datetime import datetime
from decimal import Decimal

from utms import AI, Config
from utms.cli.commands.core import Command, CommandManager
from utms.utils import print_time


def handle_resolve_command(args: argparse.Namespace, config: Config) -> None:
    """
    Handles the 'resolve' command by resolving an input string into a
    datetime or decimal value.

    This function uses the `AI` object to resolve a string input into
    a datetime or decimal object.  If the resolution is successful,
    the timestamp is printed using the `print_time` utility function.

    Args:
        args (argparse.Namespace): The parsed arguments containing the
        input string to resolve.
        config (Config): The configuration object containing necessary
        settings, such as time formats.

    Returns:
        None
    """
    ai = AI(config)
    input_string = " ".join(args.input)
    parsed_timestamp = ai.resolve_date(input_string)
    if isinstance(parsed_timestamp, (datetime, Decimal)):
        print_time(parsed_timestamp, config)


def register_resolve_command(command_manager: CommandManager) -> None:
    """
    Registers the 'resolve' command with the given command manager.

    This function creates and registers a command for resolving
    arbitrary strings into datetime values using either the
    `dateparser` library or the AI model. The command is set as the
    default action for the `resolve` command.

    Args:
        command_manager (CommandManager): The manager responsible for
        registering commands in the UTMS CLI system.

    Returns:
        None
    """
    command = Command(
        "resolve",
        None,
        lambda args: handle_resolve_command(args, command_manager.config),
        is_default=True,
    )
    command.set_help("Resolve arbitrary string into date with dateparser or with the AI")
    command.set_description("Resolve arbitrary string into date with dateparser or with the AI")

    command.add_argument(
        "input",
        type=str,
        nargs="+",
        help="String to be resolved into time",
    )

    command_manager.register_command(command)
