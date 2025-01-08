"""
Module for registering resolve-related commands.

This module provides functionality to register commands for resolving various entities
or conflicts. The `register_resolve_command` function is the main feature of this module
and is exposed through the `__all__` variable for external use.

Imports:
    - `register_resolve_command`: Function to register the resolve command.

Exports:
    - `register_resolve_command`: See `resolve.py` for implementation details.

Usage:
    Import this module to utilize the resolve command registration:
        from module_name import register_resolve_command
"""

from .resolve import register_resolve_command

__all__ = ["register_resolve_command"]
