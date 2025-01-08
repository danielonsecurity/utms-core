"""
Module for registering configuration-related commands.

This module provides functions to register commands for handling configurations,
including fetching, listing, and setting configuration options. These commands
are imported from their respective modules and exposed through the `__all__`
variable for streamlined access.

Imports:
    - `register_config_get_command`: Function to register the "get" command for configurations.
    - `register_config_list_command`: Function to register the "list" command for configurations.
    - `register_config_set_command`: Function to register the "set" command for configurations.

Exports:
    - `register_config_get_command`: See `get.py` for implementation details.
    - `register_config_list_command`: See `list.py` for implementation details.
    - `register_config_set_command`: See `set.py` for implementation details.

Usage:
    Import this module to access the configuration-related commands:
        from module_name import (
            register_config_get_command,
            register_config_list_command,
            register_config_set_command,
        )
"""

from .get import register_config_get_command
from .list import register_config_list_command
from .set import register_config_set_command

__all__ = [
    "register_config_get_command",
    "register_config_list_command",
    "register_config_set_command",
]
