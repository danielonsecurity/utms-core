from typing import Protocol, Dict, Any, Type, ClassVar

class PropertyDefinition:
    """Defines a property and its type"""
    def __init__(self, type_: Type, default: Any = None):
        self.type = type_
        self.default = default

class EntityPropertiesProtocol(Protocol):
    """Protocol for entity properties"""
    property_defs: ClassVar[Dict[str, PropertyDefinition]]
    
    def __getattr__(self, name: str) -> Any: ...
    def __setattr__(self, name: str, value: Any) -> None: ...
