"""
Argument utilities for unit-related CLI subcommands.

This module provides helper functions to add commonly used arguments
to unit-related subcommands in the UTMS CLI. These functions streamline
the process of configuring command-line argument parsers by encapsulating
reusable argument definitions.
"""

from utms.cli.commands.core.command import Command


def add_value_argument(command: Command) -> None:
    """Add value argument to unit subcommand"""
    command.add_argument(
        "value",
        type=float,
        help="The numerical value to be converted",
    )


def add_value_seconds_argument(command: Command) -> None:
    """Add value in seconds argument to unit subcommand"""
    command.add_argument(
        "-v",
        "--value",
        type=str,
        required=True,
        help="""Value of the unit in seconds""",
    )


def add_source_unit_argument(command: Command) -> None:
    """Add source_unit argument to unit subcommand"""
    command.add_argument(
        "source_unit",
        help="The unit of the value to be converted",
    )


def add_target_unit_argument(command: Command) -> None:
    """Add target_unit argument to unit subcommand"""
    command.add_argument(
        "target_unit",
        nargs="?",
        help="The desired unit to convert to. If omitted, all units are used (optional)",
    )


def add_full_argument(command: Command) -> None:
    """Add full argument to unit subcommand"""
    command.add_argument(
        "-f",
        "--full",
        action="store_true",
        help="Print result in full value, don't convert to scientific format",
    )


def add_precision_argument(command: Command) -> None:
    """Add precision argument to unit subcommand"""
    command.add_argument(
        "-p",
        "--precision",
        help="Decimal digits to print in the --full format",
    )


def add_raw_argument(command: Command) -> None:
    """Add raw argument to unit subcommand"""
    command.add_argument(
        "-r",
        "--raw",
        action="store_true",
        help="Print raw value, no colors, no extra text",
    )


def add_plt_argument(command: Command) -> None:
    """Add plt argument to unit subcommand"""
    command.add_argument(
        "-P",
        "--plt",
        action="store_true",
        default=False,
        help="Display hPLT/PLT values for each unit",
    )


def add_name_argument(command: Command) -> None:
    """Add name argument to unit subcommand"""
    command.add_argument(
        "-n",
        "--name",
        type=str,
        required=True,
        help="Full name of the unit",
    )


def add_abbreviation_argument(command: Command) -> None:
    """Add abbreviation argument to unit subcommand"""
    command.add_argument(
        "abbreviation",
        type=str,
        help="Label of the anchor to create",
    )


def add_unit_argument(command: Command) -> None:
    """Add unit argument to unit subcommand"""
    command.add_argument(
        "unit",
        type=str,
        nargs="?",
        default="s",
        help='The base unit for the conversion table ("s", "m", etc). Defaults to "s" if omitted.',
    )


def add_rows_argument(command: Command) -> None:
    """Add rows argument to unit subcommand"""
    command.add_argument(
        "rows",
        type=int,
        nargs="?",
        default=5,
        help="Number of rows before/after the base unit (default=5)",
    )


def add_columns_argument(command: Command) -> None:
    """Add columns argument to unit subcommand"""
    command.add_argument(
        "columns",
        type=int,
        nargs="?",
        default=100,
        help="Number of columns before/after the base unit (default=100)",
    )
