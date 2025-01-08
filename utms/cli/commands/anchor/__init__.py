"""
Module for registering anchor-related commands.

This module provides functions for registering anchor-related commands,
such as fetching anchor data and listing anchors. The commands are
organized into separate modules and exposed through the `__all__` variable
for easy access.

Imports:
    - `register_anchor_get_command`: Function to register the "get" command for anchors.
    - `register_anchor_list_command`: Function to register the "list" command for anchors.

Exports:
    - `register_anchor_get_command`: See `get.py` for implementation details.
    - `register_anchor_list_command`: See `list.py` for implementation details.

Usage:
    Import this module to gain access to the registered commands:
        from module_name import register_anchor_get_command, register_anchor_list_command

"""

from .get import register_anchor_get_command
from .list import register_anchor_list_command

__all__ = [
    "register_anchor_get_command",
    "register_anchor_list_command",
]
