"""Argument utilities for anchor-related CLI subcommands.

This module provides helper functions to add commonly used arguments to
anchor-related subcommands in the UTMS CLI. These functions streamline
the process of configuring command-line argument parsers by
encapsulating reusable argument definitions.
"""

from utms.cli.commands.core.command import Command


def add_anchor_list_argument(command: Command) -> None:
    """Add anchor_list argument to a anchor subcommand."""
    command.add_argument(
        "anchor_list",
        type=str,
        help="Anchor list to print by labels and groups, separated by commas (NT,UT,default)",
    )


def add_label_argument(command: Command) -> None:
    """Add label argument to a anchor subcommand."""
    command.add_argument("label", type=str, help="Label of the anchor")


def add_name_argument(command: Command, required: bool = True) -> None:
    """Add name argument to a anchor subcommand."""
    command.add_argument(
        "-n",
        "--name",
        type=str,
        required=required,
        help="Full name of the anchor",
    )


def add_value_argument(command: Command, required: bool = True) -> None:
    """Add value argument to a anchor subcommand."""
    command.add_argument(
        "-v",
        "--value",
        type=str,
        required=required,
        help="""Set the value of the anchor. If it cannot be casted to Decimal, resolve it
using dateparser/AI""",
    )


def add_groups_argument(command: Command) -> None:
    """Add groups argument to a anchor subcommand."""
    command.add_argument(
        "-g",
        "--groups",
        type=str,
        help="Comma separated list of groups for the anchor i.e. `default,fixed`",
    )


def add_precision_argument(command: Command) -> None:
    """Add precision argument to a anchor subcommand."""
    command.add_argument(
        "-p",
        "--precision",
        type=str,
        help="Precision of the anchor",
    )


def add_breakdowns_argument(command: Command) -> None:
    """Add breakdowns argument to a anchor subcommand."""
    command.add_argument(
        "-b",
        "--breakdowns",
        type=str,
        help="""List of lists of units to break down the time measurements relative to this
anchor i.e. Y;Ga,Ma;TS,GS,MS,KS,s,ms""",
    )
