"""Module for handling anchor setting commands within the `utms` command-line
interface.

This module provides the functionality to modify an existing anchor's
parameters based on the given label.  The parameters that can be
updated include the anchor's name, value, groups, precision, and
breakdowns.

Functions:
    set_anchor(args: argparse.Namespace, config: Config) -> None:
        Updates the parameters of an existing anchor based on the
        provided command-line arguments.

    register_anchor_set_command(command_manager: CommandManager) -> None:
        Registers the "anchor set" command and its associated
        arguments with the command manager.
"""

import argparse
from datetime import datetime
from decimal import Decimal, InvalidOperation

from utms import AI, Config

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
    """Updates the parameters of an existing anchor based on the provided
    arguments.

    This function allows the user to modify various properties of an
    anchor identified by its label.  It supports updating the anchor's
    name, value (resolved via dateparser/AI if necessary), groups,
    precision, and breakdowns. After updating the parameters, the
    changes are saved in the configuration.

    Args:
        args (argparse.Namespace): The parsed command-line arguments,
                                   including the anchor label and
                                   updated values for its parameters.
        config (Config): The configuration object where anchors are stored.

    Returns:
        None

    Raises:
        ValueError: If the anchor value cannot be resolved or cast to a valid type.
    """
    anchor = config.anchors.get(args.label)
    if anchor:
        if args.name:
            anchor.name = args.name
        if args.value:
            try:
                anchor.value = Decimal(args.value)
            except (InvalidOperation, ValueError):
                ai = AI(config)
                resolved_date = ai.resolve_date(args.value)
                if isinstance(resolved_date, Decimal):
                    anchor.value = resolved_date
                elif isinstance(resolved_date, datetime):
                    anchor.value = Decimal(resolved_date.timestamp())

        if args.groups:
            anchor.groups = args.groups.split(",")
        if args.precision:
            anchor.precision = Decimal(args.precision)
        if args.breakdowns:
            anchor.breakdowns = [segment.split(",") for segment in args.breakdowns.split(";")]
        config.save_anchors()
    else:
        print(f"No anchor with label {args.label} found")


def register_anchor_set_command(command_manager: CommandManager) -> None:
    """Registers the "anchor set" command with the provided command manager.

    This function defines the arguments for the "anchor set" command,
    which allows the user to modify the parameters of an existing
    anchor by its label. It associates the command with the
    `set_anchor` function that handles the anchor modification
    process.

    Args:
        command_manager (CommandManager): The command manager used to
        register the new command.

    Returns:
        None
    """
    command = Command("anchor", "set", lambda args: set_anchor(args, command_manager.config))
    command.set_help("Set an anchor parameters by label")
    command.set_description("Set the parameters of an anchor by its label")
    # Add the arguments for this command
    add_label_argument(command)
    add_name_argument(command, False)
    add_value_argument(command, False)
    add_groups_argument(command)
    add_precision_argument(command)
    add_breakdowns_argument(command)
    command_manager.register_command(command)
