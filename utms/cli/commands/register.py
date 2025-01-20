"""Module for automatically discovering and registering all commands from the
`utms.cli.commands` package.

This module provides functionality to automatically discover command
categories and the respective command registration functions within
those categories. It registers all commands with the given
`CommandManager` instance.

Functions:
    register_all_commands(command_manager: CommandManager) -> None:
        Discovers and registers all commands in the
        `utms.cli.commands` package, including its subdirectories.
"""

import importlib
import pkgutil

from .core import CommandManager


def register_all_commands(command_manager: CommandManager) -> None:
    """Automatically discovers and registers all commands from the available
    command categories in the `utms.cli.commands` package.

    This function dynamically loads all command categories
    (subdirectories) in the `utms.cli.commands` package and then
    registers the commands found in each category by calling the
    corresponding `register_` functions in each module.

    Args:
        command_manager (CommandManager): The command manager used to register commands.

    Returns:
        None

    Raises:
        ImportError: If there is an issue importing any command category or module.
        AttributeError: If any module does not contain the expected `register_` functions.
    """
    package = importlib.import_module("utms.cli.commands")

    # Iterate through all subdirectories in the `utms.cli.commands` package
    command_categories = [
        name
        for _, name, is_pkg in pkgutil.iter_modules(package.__path__)
        if is_pkg  # Only include directories (command categories)
    ]

    # Register commands for each discovered category
    for category in command_categories:
        category_package = importlib.import_module(f"utms.cli.commands.{category}")

        # Iterate through all modules in the category
        for _, module_name, _ in pkgutil.iter_modules(category_package.__path__):
            module = importlib.import_module(f"utms.cli.commands.{category}.{module_name}")

            # Register all functions in the module that start with 'register_'
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if callable(attr) and attr_name.startswith("register_"):
                    attr(command_manager)
