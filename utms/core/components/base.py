from collections.abc import MutableMapping
from typing import Any, Dict, Protocol, Type

from ..mixins.component import ComponentMixin


class SystemComponent(MutableMapping, ComponentMixin):
    """Base class for all system components with dict-like access"""

    def __init__(self, config_dir: str, component_manager=None):
        self._config_dir = config_dir
        self._component_manager = component_manager
        self._items = {}
        self._loaded = False

    def clear(self) -> None:
        """Clears all items from the manager."""
        self._items = {}
        self.logger.info(f"Manager '{type(self).__name__}' cleared all items.")

    def __getitem__(self, key):
        if not self._loaded:
            self.load()
        return self._items[key]

    def __setitem__(self, key, value):
        self._items[key] = value

    def __delitem__(self, key):
        del self._items[key]

    def __iter__(self):
        if not self._loaded:
            self.load()
        return iter(self._items)

    def __len__(self):
        if not self._loaded:
            self.load()
        return len(self._items)

    def load(self) -> None:
        """Load component data"""
        raise NotImplementedError

    def save(self) -> None:
        """Save component data"""
        raise NotImplementedError

    def is_loaded(self) -> bool:
        """Check if component is loaded"""
        return self._loaded

    def get_component(self, name: str):
        if self._component_manager:
            return self._component_manager.get_instance(name)
        return None


class ComponentManager(ComponentMixin):
    """Manages system components with lazy loading"""

    def __init__(self, config_dir: str):
        self._config_dir = config_dir
        self._components: Dict[str, SystemComponent] = {}
        self._loaded: Dict[str, bool] = {}

    def register(self, name: str, component_class: Type[SystemComponent]) -> None:
        """Register a component without loading it"""
        self.logger.debug("Component %s registered", name)
        self._components[name] = component_class(self._config_dir, self)
        self._loaded[name] = False

    def get_instance(self, name: str) -> SystemComponent:
        """Get component instance without loading it"""
        if name not in self._components:
            raise KeyError(f"No component registered for {name}")
        return self._components[name]

    def get(self, name: str) -> SystemComponent:
        """Get and load component if needed"""
        component = self.get_instance(name)
        if not self._loaded[name]:
            component.load()
            self._loaded[name] = True
        return component

    def is_loaded(self, name: str) -> bool:
        """Check if a component has been loaded"""
        return self._loaded.get(name, False)
