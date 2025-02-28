from abc import ABC, abstractmethod
from typing import Any, Dict, List

from utms.core.hy.ast.base import HyAST
from utms.core.hy.ast.node import HyNode

from .base import LoggerMixin


class PersistenceMixin(LoggerMixin):
    """Mixin for saving/loading objects to/from files."""

    @abstractmethod
    def serialize(self) -> Dict[str, Any]:
        """Convert managed objects to serializable format."""
        raise NotImplementedError

    @abstractmethod
    def deserialize(self, data: Dict[str, Any]) -> None:
        """Load objects from serialized data."""
        raise NotImplementedError


class HyPersistenceMixin(PersistenceMixin):
    """Mixin for Hy-specific file persistence."""

    @abstractmethod
    def _data_to_nodes(self, data: Dict[str, Any]) -> List[HyNode]:
        """Convert serialized data to Hy nodes."""
        raise NotImplementedError

    @abstractmethod
    def _nodes_to_data(self, nodes: List[HyNode]) -> Dict[str, Any]:
        """Convert Hy nodes to serializable data."""
        raise NotImplementedError

    def save(self, filename: str) -> None:
        """Save objects to Hy file."""
        self.logger.debug("Saving to %s", filename)
        data = self.serialize()
        nodes = self._data_to_nodes(data)

        ast_manager = HyAST()
        with open(filename, "w") as f:
            f.write(ast_manager.to_hy(nodes))
        self.logger.info("Saved %d items", len(nodes))

    def load(self, filename: str) -> None:
        """Load objects from Hy file."""
        self.logger.debug("Loading from %s", filename)
        ast_manager = HyAST()
        nodes = ast_manager.parse_file(filename)
        data = self._nodes_to_data(nodes)
        self.deserialize(data)
        self.logger.info("Loaded %d items", len(data))
