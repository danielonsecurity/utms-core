"""Module for registering the "anchor get" command.

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

import argparse

from utms import Config

from ..core import Command, CommandManager
from .helper import add_anchor_list_argument


def get_anchors(args: argparse.Namespace, config: Config) -> None:
    """Parses a comma-separated string and returns a sorted list of `Anchor`
    objects.

    This method splits the input string by commas, retrieves `Anchor` objects associated
    with each item, and adds them to a list. It also includes additional anchors based on
    groups associated with each item. The resulting list is sorted by the `value` attribute
    of the `Anchor` objects.

    Args:
        input_text (str): A comma-separated string of items, each representing
                           an anchor or group identifier.

    Returns:
        List[Anchor]: A sorted list of `Anchor` objects.

    Raises:
        ValueError: If any of the items in the input string cannot be resolved to
                    an `Anchor` object.

    Notes:
        - The method first retrieves anchors using the `get()` method, and then
          appends anchors retrieved by group using `get_anchors_by_group()`.
        - The sorting is done based on the `value` attribute of the `Anchor` objects.
    """
    anchor_list = config.anchors.get_anchors_from_str(args.anchor_list)
    for anchor in anchor_list:
        anchor.print()


def register_anchor_get_command(command_manager: CommandManager) -> None:
    """Registers the "anchor get" command.

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
    command = Command("anchor", "get", lambda args: get_anchors(args, command_manager.config))
    command.set_help("Get an anchor by label")
    command.set_description("Print one anchor properties given its label")
    # Add the arguments for this command
    add_anchor_list_argument(command)
    command_manager.register_command(command)
