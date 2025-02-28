from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Generic, List, Optional, TypeVar

from utms.core.hy.ast.node import HyNode

from ..mixins.loader import LoaderMixin

T = TypeVar("T")  # The type of objects being loaded
M = TypeVar("M")  # The type of manager being used


@dataclass
class LoaderContext:
    """Context for loading operations"""

    config_dir: str
    variables: Optional[Dict[str, Any]] = None
    dependencies: Optional[Dict[str, Any]] = None


class ComponentLoader(ABC, Generic[T, M], LoaderMixin):
    """Base class for component loaders.

    Responsible for:
    - Parsing HyNodes into intermediate format
    - Using managers to create/initialize objects
    - Handling loading context
    - Error handling and validation
    """

    def __init__(self, manager: M):
        self._manager = manager

    @abstractmethod
    def parse_definitions(self, nodes: List[HyNode]) -> Dict[str, dict]:
        """Parse HyNodes into intermediate definitions.

        Args:
            nodes: List of HyNodes to parse

        Returns:
            Dictionary mapping labels to property dictionaries
        """
        raise NotImplementedError

    @abstractmethod
    def create_object(self, label: str, properties: Dict[str, Any]) -> T:
        """Create a single object from its properties.

        Args:
            label: Object identifier
            properties: Object properties

        Returns:
            Created object
        """
        raise NotImplementedError

    def process(self, nodes: List[HyNode], context: LoaderContext) -> Dict[str, T]:
        """Process nodes into fully initialized objects.

        Args:
            nodes: List of HyNodes to process
            context: Loading context

        Returns:
            Dictionary mapping labels to initialized objects
        """
        self.logger.debug("Starting processing with context: %s", context)

        try:
            # Parse nodes into intermediate definitions
            definitions = self.parse_definitions(nodes)
            self.logger.debug("Parsed definitions: %s", list(definitions.keys()))

            # Create objects using manager
            objects = {}
            for label, properties in definitions.items():
                try:
                    obj = self.create_object(label, properties)
                    objects[label] = obj
                except Exception as e:
                    self.logger.error("Error creating object %s: %s", label, e)
                    raise

            # Load objects into manager
            self._manager.load_objects(objects)

            return objects

        except Exception as e:
            self.logger.error("Error during processing: %s", e)
            raise

    def validate_node(self, node: HyNode, expected_type: str) -> bool:
        """Validate a node's type.

        Args:
            node: Node to validate
            expected_type: Expected node type

        Returns:
            True if node is valid
        """
        if node.type != expected_type:
            self.logger.debug("Skipping node of type %s (expected %s)", node.type, expected_type)
            return False
        return True
