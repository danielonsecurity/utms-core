"""Argument utilities for daytime-related CLI subcommands.

This module provides helper functions to add commonly used arguments to
daytime-related subcommands in the UTMS CLI. These functions streamline
the process of configuring command-line argument parsers by
encapsulating reusable argument definitions.
"""

from utms.cli.commands.core.command import Command


def add_value_argument(command: Command) -> None:
    """Add value argument to daytime subcommand."""
    command.add_argument(
        "value",
        type=str,
        help="Value to be converted",
    )
