from abc import abstractmethod
from typing import Any, Dict, Generic, Optional, TypeVar

from ..mixins.manager import ManagerMixin

T = TypeVar("T")  # The type of objects managed by this manager


class BaseManager(Generic[T], ManagerMixin):
    """Base class for all managers in the system.

    Managers are responsible for:
    - Object lifecycle (creation, initialization, deletion)
    - State management
    - Persistence
    - Object relationships
    - Type-specific operations
    """

    def __init__(self, *args, **kwargs):
        self._items: Dict[str, T] = {}
        self._initialized: bool = False

    @abstractmethod
    def create(self, label: str, **kwargs) -> T:
        """Create a new managed object"""
        raise NotImplementedError

    def get(self, label: str) -> Optional[T]:
        """Get an object by its label"""
        return self._items.get(label)

    def add(self, label: str, item: T) -> None:
        """Add an existing object to the manager"""
        if label in self._items:
            raise ValueError(f"Item with label '{label}' already exists")
        self._items[label] = item

    def remove(self, label: str) -> Optional[T]:
        """Remove an object by its label"""
        return self._items.pop(label, None)

    def clear(self) -> None:
        """Remove all objects"""
        self._items.clear()

    def get_all(self) -> Dict[str, T]:
        """Get all managed objects"""
        return dict(self._items)

    @abstractmethod
    def deserialize(self, data: Dict[str, Any]) -> None:
        """Load objects from parsed data"""
        raise NotImplementedError

    @abstractmethod
    def serialize(self) -> Dict[str, Any]:
        """Save current state to serializable format"""
        raise NotImplementedError

    @property
    def is_initialized(self) -> bool:
        """Check if manager has been initialized"""
        return self._initialized

    def load_objects(self, objects: Dict[str, T]) -> None:
        self._items.update(objects)
        self._initialized = True

    def __getitem__(self, label: str) -> T:
        """Dictionary-style access to managed objects"""
        if label not in self._items:
            raise KeyError(f"No item with label '{label}'")
        return self._items[label]

    def __setitem__(self, label: str, item: T) -> None:
        """Dictionary-style setting of managed objects"""
        self.add(label, item)

    def __delitem__(self, label: str) -> None:
        """Dictionary-style removal of managed objects"""
        if label not in self._items:
            raise KeyError(f"No item with label '{label}'")
        self.remove(label)

    def __contains__(self, label: str) -> bool:
        """Support for 'in' operator"""
        return label in self._items

    def __len__(self) -> int:
        """Get number of managed objects"""
        return len(self._items)

    def __iter__(self):
        """Iterate over managed objects"""
        return iter(self._items.values())
