"""Module for handling anchor creation commands within the `utms` command-line
interface.

This module provides the functionality to create new anchors, including parsing input,
resolving values, and saving anchor configurations.

Functions:
    set_anchor(args: argparse.Namespace, config: Config) -> None:
        Creates a new anchor based on the given command-line arguments and saves it.

    register_anchor_create_command(command_manager: CommandManager) -> None:
        Registers the "anchor create" command and its associated
        arguments with the command manager.
"""

import argparse
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import List, Optional

from utms import AI
from utms import UTMSConfig as Config

from ..core import Command, CommandManager
from .helper import (
    add_breakdowns_argument,
    add_groups_argument,
    add_label_argument,
    add_name_argument,
    add_precision_argument,
    add_value_argument,
)


def set_anchor(args: argparse.Namespace, config: Config) -> None:
    """Creates a new anchor based on the provided command-line arguments and
    saves it in the configuration.

    This function checks if an anchor with the given label already
    exists. If it does, it notifies the user.  If the label is new, it
    parses and resolves the anchor's value, groups, precision, and
    breakdowns.  If the value cannot be directly converted to a
    `Decimal`, it attempts to resolve it using AI or a date parser.

    Args:
        args (argparse.Namespace): The parsed command-line arguments
        containing anchor details.
        config (Config): The configuration object where the anchor will be saved.

    Raises:
        ValueError: If the value provided for the anchor cannot be
        resolved into a valid timestamp or decimal.
    """
    if config.anchors.get(args.label):
        print(f"An anchor with label {args.label} already exists.")
        return

    groups: Optional[List[str]] = args.groups.split(",") if args.groups else None
    precision: Optional[Decimal] = Decimal(args.precision) if args.precision else None
    breakdowns: Optional[List[List[str]]] = (
        [segment.split(",") for segment in args.breakdowns.split(";")] if args.breakdowns else None
    )
    try:
        value = Decimal(args.value)
    except (InvalidOperation, ValueError) as exc:
        ai = AI(config)
        resolved_date = ai.resolve_date(args.value)
        if isinstance(resolved_date, Decimal):
            value = resolved_date
        elif isinstance(resolved_date, datetime):
            value = Decimal(resolved_date.timestamp())
        else:
            raise ValueError(f"Could not resolve {args.value}") from exc

        # anchor = AnchorConfig(
        #     args.label, args.name, value, groups=groups, precision=precision, breakdowns=breakdowns
        # )
        # config.anchors.add_anchor(anchor)

        config.save_anchors()


def register_anchor_create_command(command_manager: CommandManager) -> None:
    """Registers the "anchor create" command with the provided command manager.

    This function defines the arguments for the "anchor create"
    command, including the anchor's label, name, value, groups,
    precision, and breakdowns. It associates the command with the
    `set_anchor` function that processes the input and creates a new
    anchor.

    Args:
        command_manager (CommandManager): The command manager used to
        register the new command.

    Returns:
        None
    """
    command = Command("anchor", "create", lambda args: set_anchor(args, command_manager.config))
    command.set_help("Create a new anchor")
    command.set_description("Create a new anchor and set its parameters.")
    # Add the arguments for this command
    add_label_argument(command)
    add_name_argument(command)
    add_value_argument(command)
    add_groups_argument(command)
    add_precision_argument(command)
    add_breakdowns_argument(command)
    command_manager.register_command(command)
