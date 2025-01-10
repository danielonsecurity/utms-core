"""
Module for handling anchor deletion commands within the `utms` command-line interface.

This module provides the functionality to delete anchors by label,
ensuring that dynamic anchors (which change on each run) cannot be
deleted.

Functions:
    delete_anchor(args: argparse.Namespace, config: Config) -> None:
        Deletes an anchor based on the provided command-line arguments
        and saves the updated configuration.

    register_anchor_delete_command(command_manager: CommandManager) -> None:
        Registers the "anchor delete" command and its associated
        arguments with the command manager.
"""

import argparse

from utms import Config
from utms.cli.commands.anchor.helper import add_label_argument
from utms.cli.commands.core import Command, CommandManager


def delete_anchor(args: argparse.Namespace, config: Config) -> None:
    """
    Deletes an anchor based on the provided label and saves the updated configuration.

    This function removes an anchor from the configuration by its label. Dynamic anchors,
    which change on each run, cannot be deleted.

    Args:
        args (argparse.Namespace): The parsed command-line arguments
        containing the label of the anchor to delete.
        config (Config): The configuration object from which the anchor will be deleted.

    Returns:
        None
    """
    config.anchors.delete_anchor(args.anchor_list)
    config.save_anchors()


def register_anchor_delete_command(command_manager: CommandManager) -> None:
    """
    Registers the "anchor delete" command with the provided command manager.

    This function defines the arguments for the "anchor delete" command, which allows the user
    to delete an anchor by its label. It associates the command with the `delete_anchor` function
    that handles the anchor deletion process.

    Args:
        command_manager (CommandManager): The command manager used to register the new command.

    Returns:
        None
    """
    command = Command("anchor", "delete", lambda args: delete_anchor(args, command_manager.config))
    command.set_help("Delete an anchor by label")
    command.set_description(
        """
Delete one of the anchors. Dynamic ones cannot be deleted since they change on each run.
"""
    )
    # Add the arguments for this command
    add_label_argument(command)
    command_manager.register_command(command)
