"""
Module for registering the "anchor list" command.

This module provides functionality to register the "anchor list" command, which allows
users to list and print all configured anchors. The command is registered through the
`CommandManager` class from the core commands module.

Imports:
    - `Command`: Class used to define a command.
    - `CommandManager`: Class responsible for managing commands in the CLI.

Exports:
    - `register_anchor_list_command`: Function to register the "anchor list" command.

Usage:
    Import this module and use the `register_anchor_list_command` function to add the
    "anchor list" command to your `CommandManager` instance:
        from module_name import register_anchor_list_command

        register_anchor_list_command(command_manager)
"""

from utms.cli.commands.core import Command, CommandManager


def register_anchor_list_command(command_manager: CommandManager) -> None:
    """
    Registers the "anchor list" command.

    This function sets up and registers the "anchor list" command with the provided
    command manager. The command allows users to list all configured anchors and print
    their details to the console.

    Args:
        command_manager (CommandManager): The command manager responsible for
            registering and managing commands.

    Command Details:
        - Name: "anchor list"
        - Description: Lists all configured anchors.
        - Help: "Print anchors"
        - Default Command: This command is set as the default for the "anchor" group.

    Example Usage:
        Assuming `command_manager` is an instance of `CommandManager`:
            register_anchor_list_command(command_manager)

        In CLI:
            anchor list
    """
    anchor_manager = command_manager.config.anchors
    command = Command("anchor", "list", lambda _: anchor_manager.print(), is_default=True)
    command.set_help("Print anchors")
    command.set_description("List all configured anchors")
    command_manager.register_command(command)
