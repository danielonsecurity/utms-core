"""
Module for registering unit-related commands in the UTMS CLI system.

This module imports and aggregates the functions for the following unit-related commands:
- `register_unit_convert_command`: Registers the command to convert between units.
- `register_unit_list_command`: Registers the command to list all available units.
- `register_unit_table_command`: Registers the command to display a
  conversion table for a specific unit.

By importing this module, the unit commands are made available for
registration within the UTMS CLI system.

Exports:
    - `register_unit_convert_command`: Command for converting between units.
    - `register_unit_list_command`: Command for listing available units.
    - `register_unit_table_command`: Command for displaying a unit conversion table.
"""

from .convert import register_unit_convert_command
from .list import register_unit_list_command
from .table import register_unit_table_command

__all__ = [
    "register_unit_table_command",
    "register_unit_list_command",
    "register_unit_convert_command",
]
