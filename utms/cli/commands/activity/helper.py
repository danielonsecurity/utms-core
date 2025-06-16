"""Argument utilities for start-related CLI subcommands."""

from ..core import Command

def add_entity_identifier_argument(command: Command) -> None:
    """Add the entity_identifier positional argument."""
    command.add_argument(
        "entity_identifier",
        type=str,
        help="The identifier of the entity to start, in 'type:category:name' format.",
    )
