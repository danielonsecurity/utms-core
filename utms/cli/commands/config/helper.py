"""Argument utilities for config-related CLI subcommands.

This module provides helper functions to add commonly used arguments to
config-related subcommands in the UTMS CLI. These functions streamline
the process of configuring command-line argument parsers by
encapsulating reusable argument definitions.
"""

from utms.cli.commands.core.command import Command


def add_key_argument(command: Command) -> None:
    """Add key argument to config subcommand."""
    command.add_argument(
        "key",
        type=str,
        help="Config key",
    )


def add_value_argument(command: Command) -> None:
    """Add value argument to config subcommand."""
    command.add_argument(
        "value",
        type=str,
        help="Config value",
    )
