from typing import Dict, Type, Any, Protocol
from utms.utils import get_logger
from collections.abc import MutableMapping

class SystemComponent(MutableMapping):
    """Base class for all system components with dict-like access"""
    
    def __init__(self, config_dir: str):
        self._config_dir = config_dir
        self._items = {}
        self._loaded = False
        self._logger = get_logger(f"core.components.{self.__class__.__name__.lower()}")

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



class ComponentManager:
    """Manages system components with lazy loading"""
    def __init__(self, config_dir: str):
        self._config_dir = config_dir
        self._components: Dict[str, SystemComponent] = {}
        self._loaded: Dict[str, bool] = {}

    def register(self, name: str, component_class: Type[SystemComponent]) -> None:
        """Register a component without loading it"""
        self._components[name] = component_class(self._config_dir)
        self._loaded[name] = False

    def get(self, name: str) -> SystemComponent:
        """Get a component, loading it if necessary"""
        if name not in self._components:
            raise KeyError(f"No component registered for {name}")
        
        if not self._loaded[name]:
            self._components[name].load()
            self._loaded[name] = True
            
        return self._components[name]

    def is_loaded(self, name: str) -> bool:
        """Check if a component has been loaded"""
        return self._loaded.get(name, False)
