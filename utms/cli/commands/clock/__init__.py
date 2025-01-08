"""
Module for registering clock-related commands.

This module provides functionality to register commands related to clock operations.
The primary function, `register_clock_command`, is imported and exposed through the
`__all__` variable for external use.

Imports:
    - `register_clock_command`: Function to register clock commands.

Exports:
    - `register_clock_command`: See `clock.py` for implementation details.

Usage:
    Import this module to utilize the clock command registration:
        from module_name import register_clock_command
"""

from .clock import register_clock_command

__all__ = ["register_clock_command"]
