import importlib
import inspect
import logging
import pkgutil
from typing import List, Optional, Type

from utms.core.logger import get_logger

from .base import NodePlugin, UTMSPlugin
from .registry import plugin_registry


def discover_plugins(
    base_package: str = "utms.core.plugins.elements", plugin_types: Optional[List[Type]] = None
) -> List[Type]:
    """
    Automatically discover and load plugins from a specified package.

    Args:
        base_package: Base package to search for plugins
        plugin_types: Optional list of plugin base classes to filter

    Returns:
        List of discovered plugin classes
    """
    discovered_plugins = []
    logger = get_logger()

    if plugin_types is None:
        plugin_types = [NodePlugin, UTMSPlugin]

    try:
        package = importlib.import_module(base_package)

        for loader, module_name, is_pkg in pkgutil.iter_modules(package.__path__):
            full_module_name = f"{base_package}.{module_name}"

            try:
                module = importlib.import_module(full_module_name)

                for name, obj in inspect.getmembers(module):
                    if (
                        inspect.isclass(obj)
                        and any(issubclass(obj, plugin_type) for plugin_type in plugin_types)
                        and obj not in plugin_types
                    ):

                        # Determine plugin type and register accordingly
                        if issubclass(obj, NodePlugin):
                            plugin_registry.register_node_plugin(obj)
                        elif issubclass(obj, UTMSPlugin):
                            plugin_registry.register_generic_plugin(obj)

                        discovered_plugins.append(obj)
                        logger.info(f"Discovered plugin: {obj.__name__}")

            except ImportError as e:
                logger.warning(f"Could not import module {full_module_name}: {e}")

    except ImportError:
        logger.warning(f"No plugins found in {base_package}")

    return discovered_plugins


def initialize_plugins(system_context: dict = None):
    """
    Initialize all discovered plugins with optional system context.

    Args:
        system_context: Dictionary of system-wide configuration and resources
    """
    logger = logging.getLogger("utms.plugin_initialization")

    if system_context is None:
        system_context = {}

    # Initialize node plugins
    for node_type in plugin_registry.list_node_plugins():
        plugin = plugin_registry.get_node_plugin(node_type)
        try:
            plugin.initialize(system_context)
            logger.info(f"Initialized node plugin: {plugin.name}")
        except Exception as e:
            logger.error(f"Failed to initialize node plugin {plugin.name}: {e}")

    # Initialize generic plugins
    for plugin_name in plugin_registry.list_generic_plugins():
        plugin = plugin_registry.get_generic_plugin(plugin_name)
        try:
            plugin.initialize(system_context)
            logger.info(f"Initialized generic plugin: {plugin.name}")
        except Exception as e:
            logger.error(f"Failed to initialize generic plugin {plugin.name}: {e}")
