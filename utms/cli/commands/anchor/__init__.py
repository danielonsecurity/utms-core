"""Module for registering anchor-related commands.

This module provides functions for registering anchor-related commands,
such as fetching anchor data and listing anchors. The commands are
organized into separate modules and exposed through the `__all__` variable
for easy access.

Imports:
    - `register_anchor_get_command`: Function to register the "get" command for anchors.
    - `register_anchor_set_command`: Function to register the "set" command for anchors.
    - `register_anchor_list_command`: Function to register the "list" command for anchors.

Exports:
    - `register_anchor_get_command`: See `get.py` for implementation details.
    - `register_anchor_set_command`: See `set.py` for implementation details.
    - `register_anchor_list_command`: See `list.py` for implementation details.

Usage:
    Import this module to gain access to the registered commands:
        from module_name import register_anchor_get_command,
        register_anchor_get_command, register_anchor_list_command
"""

from .create import register_anchor_create_command
from .delete import register_anchor_delete_command
from .get import register_anchor_get_command
from .list import register_anchor_list_command
from .set import register_anchor_set_command
