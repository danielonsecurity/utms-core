from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from utms.utms_types import HyNode


class UTMSPlugin(ABC):
    """
    Base plugin interface for all UTMS plugins.
    Provides a generic, system-wide plugin contract.

    Responsibilities:
    - Provide a unique identifier for the plugin
    - Define version information
    - Allow system-wide initialization
    - Support basic plugin metadata and configuration
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name/identifier for the plugin"""

    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version"""

    @property
    def description(self) -> Optional[str]:
        """Optional plugin description"""
        return None

    @abstractmethod
    def initialize(self, system_context: Dict[str, Any]):
        """
        Initialize the plugin with system-wide context.

        Args:
            system_context: A dictionary containing system-wide configuration
                            and shared resources
        """

    def configure(self, config: Dict[str, Any]):
        """
        Optional method to configure the plugin after initialization.

        Args:
            config: Plugin-specific configuration dictionary
        """
        pass

    def validate(self) -> bool:
        """
        Optional validation method to check plugin readiness.

        Returns:
            bool: Whether the plugin is valid and ready to use
        """
        return True


class NodePlugin(UTMSPlugin):
    """
    Specialized plugin for handling specific node types in the UTMS AST.

    Responsibilities:
    - Define a specific node type
    - Provide parsing logic for that node type
    - Provide formatting logic for that node type
    - Extend the base UTMSPlugin with node-specific methods
    """

    @property
    @abstractmethod
    def node_type(self) -> str:
        """
        The specific type of node this plugin handles.

        Returns:
            str: Node type identifier (e.g., 'custom-set-config', 'def-anchor')
        """

    @abstractmethod
    def parse(self, expression: Any) -> "HyNode":
        """
        Parse a Hy language expression into a HyNode.

        Args:
            expression: The Hy language expression to parse

        Returns:
            HyNode: The parsed node representation
        """

    @abstractmethod
    def format(self, node: "HyNode") -> list[str]:
        """
        Format a HyNode back into Hy language representation.

        Args:
            node: The HyNode to format

        Returns:
            list[str]: Formatted Hy language lines
        """
