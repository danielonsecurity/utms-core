"""
Module for command-related classes and management.

This module provides the core classes for defining, managing, and organizing commands.
It includes abstractions for individual commands, command managers, and command hierarchies.
These classes are imported and exposed through the `__all__` variable for external use.

Imports:
    - `Command`: Class representing an individual command.
    - `CommandManager`: Class for managing and orchestrating commands.
    - `CommandHierarchy`: Class for organizing commands into hierarchical structures.

Exports:
    - `Command`: See `command.py` for implementation details.
    - `CommandManager`: See `command_manager.py` for implementation details.
    - `CommandHierarchy`: See `hierarchy.py` for implementation details.

Usage:
    Import this module to work with commands, their management, and hierarchies:
        from module_name import Command, CommandManager, CommandHierarchy
"""

from .command import Command
from .command_manager import CommandManager
from .hierarchy import CommandHierarchy

__all__ = ["Command", "CommandManager", "CommandHierarchy"]
