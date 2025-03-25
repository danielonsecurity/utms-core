from typing import Dict, List, Optional, Type

from .base import NodePlugin, UTMSPlugin


class PluginRegistry:
    """
    Central registry for managing UTMS plugins.

    Supports flexible plugin registration, retrieval, and management.
    Designed to be extensible and follow UTMS's flexible philosophy.
    """

    def __init__(self):
        # Separate registries for different plugin types
        self._node_plugins: Dict[str, Type[NodePlugin]] = {}
        self._generic_plugins: Dict[str, Type[UTMSPlugin]] = {}

        # Track plugin instances for lifecycle management
        self._active_node_plugins: Dict[str, NodePlugin] = {}
        self._active_generic_plugins: Dict[str, UTMSPlugin] = {}

    def register_node_plugin(self, plugin_class: Type[NodePlugin], overwrite: bool = False):
        """
        Register a node plugin.

        Args:
            plugin_class: The plugin class to register
            overwrite: If True, allows overwriting existing plugin for a node type

        Raises:
            ValueError if plugin already exists and overwrite is False
        """
        instance = plugin_class()
        node_type = instance.node_type

        if node_type in self._node_plugins and not overwrite:
            raise ValueError(f"Node plugin for {node_type} already registered")

        self._node_plugins[node_type] = plugin_class

    def register_generic_plugin(self, plugin_class: Type[UTMSPlugin], overwrite: bool = False):
        """
        Register a generic plugin.

        Args:
            plugin_class: The plugin class to register
            overwrite: If True, allows overwriting existing plugin

        Raises:
            ValueError if plugin already exists and overwrite is False
        """
        instance = plugin_class()
        plugin_name = instance.name

        if plugin_name in self._generic_plugins and not overwrite:
            raise ValueError(f"Plugin {plugin_name} already registered")

        self._generic_plugins[plugin_name] = plugin_class

    def get_node_plugin(self, node_type: str) -> Optional[NodePlugin]:
        """
        Retrieve a node plugin for a specific node type.

        Args:
            node_type: The type of node to get a plugin for

        Returns:
            Instantiated NodePlugin or None if not found
        """
        plugin_class = self._node_plugins.get(node_type)
        if plugin_class:
            # Cache and return plugin instance
            if node_type not in self._active_node_plugins:
                self._active_node_plugins[node_type] = plugin_class()
            return self._active_node_plugins[node_type]
        return None

    def get_generic_plugin(self, plugin_name: str) -> Optional[UTMSPlugin]:
        """
        Retrieve a generic plugin by name.

        Args:
            plugin_name: Name of the plugin to retrieve

        Returns:
            Instantiated UTMSPlugin or None if not found
        """
        plugin_class = self._generic_plugins.get(plugin_name)
        if plugin_class:
            # Cache and return plugin instance
            if plugin_name not in self._active_generic_plugins:
                self._active_generic_plugins[plugin_name] = plugin_class()
            return self._active_generic_plugins[plugin_name]
        return None

    def list_node_plugins(self) -> List[str]:
        """List all registered node plugin types"""
        return list(self._node_plugins.keys())

    def list_generic_plugins(self) -> List[str]:
        """List all registered generic plugins"""
        return list(self._generic_plugins.keys())

    def clear(self):
        """
        Clear all registered plugins.
        Useful for testing or resetting the system.
        """
        self._node_plugins.clear()
        self._generic_plugins.clear()
        self._active_node_plugins.clear()
        self._active_generic_plugins.clear()


# Global singleton registry
plugin_registry = PluginRegistry()
