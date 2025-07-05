# utms.core.loaders.base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass, field  # Added field for default_factory
from typing import Any, Dict, Generic, List, Optional, TypeVar

# Assuming BaseManager is defined and importable
from utms.core.managers.base import BaseManager  # Or correct path
# Corrected import path if LoaderMixin is in utms.core.mixins.loader
from utms.core.mixins.loader import LoaderMixin  # Assuming this path
from utms.utms_types import HyNode  # Assuming HyNode is defined in utms.utms_types

# If LoaderMixin is in utms.core.mixins.base (as in earlier files):
# from utms.core.mixins.base import LoaderMixin # Or from wherever LoaderMixin actually is


T = TypeVar("T")  # The type of objects being loaded
M = TypeVar("M", bound=BaseManager)  # Ensure TManager is bound to BaseManager or its protocol


@dataclass
class LoaderContext:
    """Context for loading operations"""

    config_dir: str
    # Use field(default_factory=dict) for mutable defaults
    variables: Dict[str, Any] = field(default_factory=dict)
    dependencies: Optional[Dict[str, Any]] = None  # Or specific type
    current_entity_type: Optional[str] = None  # e.g., "task" (lowercase string)
    current_category: Optional[str] = None  # e.g., "work", "default" (lowercase string)
    current_entity_schema: Optional[Dict[str, Any]] = None  # Stores the attributes_schema dict
    known_complex_type_schemas: Optional[Dict[str, Any]] = None  # Stores all complex type schemas


class ComponentLoader(
    ABC, Generic[T, M], LoaderMixin
): 
    """Base class for component loaders.

    Responsible for:
    - Parsing HyNodes into intermediate format
    - Using managers to create/initialize objects
    - Handling loading context
    - Error handling and validation
    """

    def __init__(self, manager: M):
        super().__init__()  # Call super for LoggerMixin if it has an __init__
        self._manager = manager
        self.context: Optional[LoaderContext] = None  # Allow context to be set, good

    @abstractmethod
    def parse_definitions(
        self, nodes: List[HyNode]
    ) -> Dict[str, dict]:  # dict for properties is fine
        """Parse HyNodes into intermediate definitions.

        Args:
            nodes: List of HyNodes to parse

        Returns:
            Dictionary mapping labels to property dictionaries
        """
        raise NotImplementedError

    @abstractmethod
    def create_object(
        self, label: str, properties: Dict[str, Any]
    ) -> T:  # label is key from parse_definitions
        """Create a single object from its properties.

        Args:
            label: Object identifier (unique key from parse_definitions)
            properties: Object properties (the dict associated with the label)

        Returns:
            Created object
        """
        raise NotImplementedError

    def process(self, nodes: List[HyNode], context: LoaderContext) -> Dict[str, T]:
        """
        Process a list of HyNodes: parse definitions, then create objects.
        It is assumed that self.create_object (when calling self._manager.create or self._manager.add)
        is responsible for storing the created object in the manager.
        Returns a dictionary of created objects, keyed by their definition key from parse_definitions.
        """
        self.logger.debug("Starting ComponentLoader processing with context: %s", context)
        self.context = context

        try:
            definitions = self.parse_definitions(nodes)
            self.logger.debug("Parsed definitions: %s", list(definitions.keys()))

            created_objects: Dict[str, T] = {}
            for label, properties in definitions.items():  # label is the key from parse_definitions
                try:
                    # self.create_object is responsible for calling self._manager.create (or add)
                    # which populates self._manager._items.
                    obj = self.create_object(label, properties)
                    created_objects[label] = obj
                except Exception as e:
                    self.logger.error(
                        "Error creating object for definition '%s': %s", label, e, exc_info=True
                    )
                    raise

            # REMOVED: self._manager.load_objects(objects)
            # This was potentially causing issues if create_object also added to manager.
            # The manager should be populated by its own create/add methods called within create_object.
            self.logger.debug(
                f"ComponentLoader processing finished. {len(created_objects)} objects processed/created via manager."
            )
            return created_objects

        except Exception as e:
            self.logger.error("Error during ComponentLoader processing: %s", e, exc_info=True)
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
            self.logger.warning("Skipping node of type %s (expected %s)", node.type, expected_type)
            return False
        return True
