"""
Unit creation commands for the UTMS CLI.

This module defines functionality for adding a new unit to the UTMS configuration.
It includes the core logic for creating units and registering the associated CLI
command to the command manager.

Functions:
    create_unit(args: argparse.Namespace, config: Config) -> None
        Creates a new unit and updates the configuration if the unit does not already exist.

    register_unit_create_command(command_manager: CommandManager) -> None
        Registers the 'unit create' command with the CommandManager,
        enabling users to add new units.
"""

import argparse
from decimal import Decimal

from utms import Config
from utms.cli.commands.core import Command, CommandManager
from utms.cli.commands.unit.helper import (
    add_abbreviation_argument,
    add_name_argument,
    add_value_seconds_argument,
)


def create_unit(args: argparse.Namespace, config: Config) -> None:
    """
    Create a new unit and add it to the UTMS configuration.

    This function checks if a unit with the given abbreviation already exists.
    If not, it adds the unit with the provided name, abbreviation, and value
    (in seconds) to the configuration and saves the changes.

    Args:
        args (argparse.Namespace): Parsed command-line arguments containing
            the unit name, abbreviation, and value in seconds.
        config (Config): The UTMS configuration instance for managing units.
    """
    if config.units.get_unit(args.abbreviation):
        print(f"An unit with abbreviation {args.abbreviation} already exists.")
        return

    config.units.add_unit(args.name, args.abbreviation, Decimal(args.value))
    config.save_units()


def register_unit_create_command(command_manager: CommandManager) -> None:
    """
    Register the 'unit create' command with the CommandManager.

    This function defines a new CLI command for creating units and associates it
    with the `CommandManager`. It configures the command's arguments and their
    help text before registering the command.

    Args:
        command_manager (CommandManager): The command manager instance to register
            the 'unit create' command with.
    """
    command = Command("unit", "create", lambda args: create_unit(args, command_manager.config))
    command.set_help("Create a new unit")
    command.set_description("Create a new unit")
    # Add the arguments for this command
    add_abbreviation_argument(command)
    add_value_seconds_argument(command)
    add_name_argument(command)
    command_manager.register_command(command)
