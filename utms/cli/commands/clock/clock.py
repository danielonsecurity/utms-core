"""
Module for registering the "clock" command.

This module provides functionality to register the "clock" command, which runs a clock
displaying time both in decimal and duodecimal units. The command is registered using
the `CommandManager` class from the core commands module.

Imports:
    - `Command`: Class used to define a command.
    - `CommandManager`: Class responsible for managing commands in the CLI.
    - `run_clock`: Function from the `clock` module that runs the clock.

Exports:
    - `register_clock_command`: Function to register the "clock" command.

Usage:
    Import this module and use the `register_clock_command` function to add the
    "clock" command to your `CommandManager` instance:
        from module_name import register_clock_command

        register_clock_command(command_manager)
"""

from utms.cli.commands.core import Command, CommandManager
from utms.clock import run_clock


def register_clock_command(command_manager: CommandManager) -> None:
    """
    Registers the "clock" command.

    This function sets up and registers the "clock" command with the provided
    command manager. The command runs a clock that displays time in both decimal
    and duodecimal units.

    Args:
        command_manager (CommandManager): The command manager responsible for
            registering and managing commands.

    Command Details:
        - Name: "clock"
        - Description: Runs a clock showing time in decimal and duodecimal formats.
        - Help: "Run clock"
        - Default Command: This command is set as the default for the "clock" group.

    Example Usage:
        Assuming `command_manager` is an instance of `CommandManager`:
            register_clock_command(command_manager)

        In CLI:
            clock
    """
    command = Command(
        "clock",
        None,
        lambda _: run_clock(),
        is_default=True,
    )
    command.set_help("Run clock")
    command.set_description("Run a clock showing time both in decimal units and duodecimal ones")

    command_manager.register_command(command)
