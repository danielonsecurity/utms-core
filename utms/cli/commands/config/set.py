"""
Module for registering the "config set" command.

This module provides functionality to register the "config set" command, which allows
users to set a configuration value for a specific key. The command is registered using
the `CommandManager` class from the core commands module.

Imports:
    - `Command`: Class used to define a command.
    - `CommandManager`: Class responsible for managing commands in the CLI.

Exports:
    - `register_config_set_command`: Function to register the "config set" command.

Usage:
    Import this module and use the `register_config_set_command` function to add the
    "config set" command to your `CommandManager` instance:
        from module_name import register_config_set_command

        register_config_set_command(command_manager)
"""

from utms.cli.commands.core import Command, CommandManager


def register_config_set_command(command_manager: CommandManager) -> None:
    """
    Registers the "config set" command.

    This function sets up and registers the "config set" command with the provided
    command manager. The command allows users to set the value of a specific configuration
    option based on its key.

    Args:
        command_manager (CommandManager): The command manager responsible for
            registering and managing commands.

    Command Details:
        - Name: "config set"
        - Description: Sets a configuration value based on the provided key and value.
        - Help: "Set a configuration value"

    Command Arguments:
        - `key` (str): The key of the configuration option to set. This argument
          is required.
        - `value` (str): The value to assign to the specified configuration key.
          This argument is required.

    Example Usage:
        Assuming `command_manager` is an instance of `CommandManager`:
            register_config_set_command(command_manager)

        In CLI:
            config set <key> <value>
    """
    command = Command(
        "config", "set", lambda args: command_manager.config.set_value(args.key, args.value)
    )
    command.set_help("Set a configuration value")
    command.set_description("Set the config option from its key")
    # Add the arguments for this command
    command.add_argument(
        "key",
        type=str,
        help="Config key to set",
    )

    command.add_argument(
        "value",
        type=str,
        help="Config value to set",
    )

    command_manager.register_command(command)
