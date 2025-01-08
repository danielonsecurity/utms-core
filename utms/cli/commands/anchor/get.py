"""
Module for registering the "anchor get" command.

This module provides functionality to register the "anchor get" command, which allows users
to retrieve and print the properties of a specific anchor identified by its label. The command
is registered using the `CommandManager` class from the core commands module.

Imports:
    - `Command`: Class used to define a command.
    - `CommandManager`: Class responsible for managing commands in the CLI.

Exports:
    - `register_anchor_get_command`: Function to register the "anchor get" command.

Usage:
    Import this module and use the `register_anchor_get_command` function to add the
    "anchor get" command to your `CommandManager` instance:
        from module_name import register_anchor_get_command

        register_anchor_get_command(command_manager)
"""

from utms.cli.commands.core import Command, CommandManager


def register_anchor_get_command(command_manager: CommandManager) -> None:
    """
    Registers the "anchor get" command.

    This function sets up and registers the "anchor get" command with the provided
    command manager. The command allows users to retrieve and print the properties
    of a specific anchor by its label.

    Args:
        command_manager (CommandManager): The command manager responsible for
            registering and managing commands.

    Command Details:
        - Name: "anchor get"
        - Description: Prints the properties of a specific anchor identified by its label.
        - Help: "Get an anchor by label"

    Command Arguments:
        - `label` (str): The label of the anchor to retrieve and print. This argument
          is required.

    Example Usage:
        Assuming `command_manager` is an instance of `CommandManager`:
            register_anchor_get_command(command_manager)

        In CLI:
            anchor get <label>
    """
    anchor_manager = command_manager.config.anchors
    command = Command("anchor", "get", lambda args: anchor_manager.print(args.label))
    command.set_help("Get an anchor by label")
    command.set_description("Print one anchor properties given its label")
    # Add the arguments for this command
    command.add_argument(
        "label",
        type=str,
        help="Anchor label to print",
    )

    command_manager.register_command(command)
