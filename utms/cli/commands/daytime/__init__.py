"""
Module for registering daytime-related commands.

This module provides functions to register commands for handling daytime operations,
such as timetable management and conversions. These commands are imported from their
respective modules and exposed through the `__all__` variable for streamlined access.

Imports:
    - `register_daytime_convert_command`: Function to register the "convert" command
      for daytime operations.
    - `register_daytime_timetable_command`: Function to register the "timetable"
      command for daytime scheduling.

Exports:
    - `register_daytime_convert_command`: See `convert.py` for implementation details.
    - `register_daytime_timetable_command`: See `timetable.py` for implementation details.

Usage:
    Import this module to use the daytime-related commands:
        from module_name import (
            register_daytime_convert_command,
            register_daytime_timetable_command,
        )
"""

from .convert import register_daytime_convert_command
from .timetable import register_daytime_timetable_command

__all__ = ["register_daytime_timetable_command", "register_daytime_convert_command"]
