"""Argument utilities for resolve-related CLI subcommands.

This module provides helper functions to add commonly used arguments to
resolve-related subcommands in the UTMS CLI. These functions streamline
the process of configuring command-line argument parsers by
encapsulating reusable argument definitions.
"""

from ..core import Command


def add_anchor_list_argument(command: Command) -> None:
    """Add anchor_list argument to resolve subcommand."""
    command.add_argument(
        "-a",
        "--anchor_list",
        type=str,
        help="Anchor/Anchor groups to display",
    )


def add_units_argument(command: Command) -> None:
    """Add units argument to resolve subcommand."""
    command.add_argument(
        "-u",
        "--units",
        type=str,
        help="""List of lists of units to break down the time measurements relative to
this anchor i.e. Y;Ga,Ma;TS,GS,MS,KS,s,ms. Note: the actual anchor
breakdowns don't change.
        """,
    )


def add_plt_argument(command: Command) -> None:
    """Add plt argument to resolve subcommand."""
    command.add_argument(
        "-p",
        "--plt",
        action="store_true",
        default=False,
        help="Display hPLT/PLT values",
    )


def add_input_argument(command: Command) -> None:
    """Add input argument to resolve subcommand."""
    command.add_argument(
        "input",
        type=str,
        nargs="+",
        help="String to be resolved into time",
    )
