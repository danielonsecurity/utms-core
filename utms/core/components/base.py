from collections.abc import MutableMapping
from typing import Any, Dict, Protocol, Type, Optional

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

    def __bool__(self):
        return True

    def __getitem__(self, key):
        if not self._loaded:
            self.logger.warning(f"Component '{type(self).__name__}' accessed before being loaded.")
        return self._items[key]

    def __setitem__(self, key, value):
        self._items[key] = value

    def __delitem__(self, key):
        del self._items[key]

    def __iter__(self):
        if not self._loaded:
            self.logger.warning(f"Component '{type(self).__name__}' iterated before being loaded.")
        return iter(self._items)

    def __len__(self):
        if not self._loaded:
            self.logger.warning(f"Component '{type(self).__name__}' had len() called before being loaded.")
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
            return self._component_manager.get(name)
        return None


class ComponentManager(ComponentMixin):
    """Manages system components with lazy loading"""

    def __init__(self, config_dir: str):
        self._config_dir = config_dir
        self._components: Dict[str, SystemComponent] = {}
        # The _loaded flag is on the component itself, so we don't need it here.

    def register(self, name: str, component_class: Type[SystemComponent]) -> None:
        """Register a component by instantiating it."""
        self.logger.debug("Component %s registered", name)
        # Store the component instance, not the class.
        self._components[name] = component_class(self._config_dir, self)

    def get_instance(self, name: str) -> Optional[SystemComponent]:
        """Gets a component instance without triggering its load() method."""
        if name not in self._components:
            self.logger.error(f"No component registered for '{name}'")
            return None
        return self._components[name]

    def get(self, name: str) -> Optional[SystemComponent]:
        """
        Gets a component by name, loading it if it hasn't been loaded yet.
        This is the lazy-loading public interface.
        """
        instance = self.get_instance(name)
        if instance and not instance.is_loaded():
            self.logger.debug(f"Lazy loading component on demand: '{name}'")
            instance.load()
        return instance
