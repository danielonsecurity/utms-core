"""
Module for registering the "config get" command.

This module provides functionality to register the "config get" command, which allows
users to retrieve a configuration value by its key. The command is registered using the
`CommandManager` class from the core commands module.

Imports:
    - `Command`: Class used to define a command.
    - `CommandManager`: Class responsible for managing commands in the CLI.

Exports:
    - `register_config_get_command`: Function to register the "config get" command.

Usage:
    Import this module and use the `register_config_get_command` function to add the
    "config get" command to your `CommandManager` instance:
        from module_name import register_config_get_command

        register_config_get_command(command_manager)
"""

from utms.cli.commands.core import Command, CommandManager


def register_config_get_command(command_manager: CommandManager) -> None:
    """
    Registers the "config get" command.

    This function sets up and registers the "config get" command with the provided
    command manager. The command allows users to retrieve and print the value of a
    specific configuration option based on its key.

    Args:
        command_manager (CommandManager): The command manager responsible for
            registering and managing commands.

    Command Details:
        - Name: "config get"
        - Description: Retrieves a configuration value based on the provided key.
        - Help: "Get a configuration value"

    Command Arguments:
        - `key` (str): The key of the configuration option to retrieve. This argument
          is required.

    Example Usage:
        Assuming `command_manager` is an instance of `CommandManager`:
            register_config_get_command(command_manager)

        In CLI:
            config get <key>
    """
    command = Command(
        "config", "get", lambda args: print(command_manager.config.get_value(args.key))
    )
    command.set_help("Get a configuration value")
    command.set_description("Get the config option from its key")
    # Add the arguments for this command
    command.add_argument(
        "key",
        type=str,
        help="Config key to get",
    )

    command_manager.register_command(command)
