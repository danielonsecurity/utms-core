"""
Module for registering the "config list" command.

This module provides functionality to register the "config list" command, which allows
users to list all available configuration options. The command is registered using the
`CommandManager` class from the core commands module.

Imports:
    - `Command`: Class used to define a command.
    - `CommandManager`: Class responsible for managing commands in the CLI.

Exports:
    - `register_config_list_command`: Function to register the "config list" command.

Usage:
    Import this module and use the `register_config_list_command` function to add the
    "config list" command to your `CommandManager` instance:
        from module_name import register_config_list_command

        register_config_list_command(command_manager)
"""

from utms.cli.commands.core import Command, CommandManager


def register_config_list_command(command_manager: CommandManager) -> None:
    """
    Registers the "config list" command.

    This function sets up and registers the "config list" command with the provided
    command manager. The command allows users to print and list all available configuration
    options.

    Args:
        command_manager (CommandManager): The command manager responsible for
            registering and managing commands.

    Command Details:
        - Name: "config list"
        - Description: Lists all available configuration options.
        - Help: "Print config"
        - Default Command: This command is set as the default for the "config" group.

    Example Usage:
        Assuming `command_manager` is an instance of `CommandManager`:
            register_config_list_command(command_manager)

        In CLI:
            config list
    """
    command = Command("config", "list", lambda _: command_manager.config.print(), is_default=True)
    command.set_help("Print config")
    command.set_description("List all configuration options")
    command_manager.register_command(command)
