from typing import Any, Dict, ClassVar, List, get_origin, get_args
from utms.utms_types.entity.protocols import TimeEntityProtocol
from utms.utms_types.entity.types import AttributeDefinition
from utms.utms_types.entity.attributes import CORE_ATTRIBUTES

class TimeEntity(TimeEntityProtocol):
    """Base class for all time entities"""
    
    BASE_ATTRIBUTES: ClassVar[Dict[str, AttributeDefinition]] = {
        'name': AttributeDefinition(str, required=True),
    }
    attributes: ClassVar[Dict[str, AttributeDefinition]] = {
        **CORE_ATTRIBUTES,
        **BASE_ATTRIBUTES,
    }

    @classmethod
    def get_all_attributes(cls) -> Dict[str, AttributeDefinition]:
        """Get all attributes including base attributes"""
        return {
            **cls.BASE_ATTRIBUTES,
            **cls.attributes
        }


    def __init__(self, name: str):
        object.__setattr__(self, '_attrs', {})
        self._attrs["name"] = name
        
        # Then initialize default values
        for attr_name, attr_def in self.get_all_attributes().items():
            if attr_name != "name":
                if hasattr(attr_def, "default_factory") and attr_def.default_factory is not None:
                    setattr(self, attr_name, attr_def.default_factory())
                elif hasattr(attr_def, "default") and  attr_def.default is not None:
                    setattr(self, attr_name, attr_def.default)

    def _validate_type(self, value: Any, expected_type: type) -> bool:
        """Validate type, handling generic types like List"""
        origin = get_origin(expected_type)
        if origin is None:  # Not a generic type
            return isinstance(value, expected_type)
        
        # Handle generic types
        if origin is list:
            return (isinstance(value, list) and 
                   all(isinstance(item, get_args(expected_type)[0]) 
                       for item in value))
        if origin is dict:
            key_type, value_type = get_args(expected_type)
            return (isinstance(value, dict) and
                   all(isinstance(k, key_type) for k in value.keys()) and
                   all(isinstance(v, value_type) for v in value.values()))
        return isinstance(value, origin)



    def __getattr__(self, name: str) -> Any:
        if name in self.get_all_attributes():
            return self._attrs.get(name)
        raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith('_'):  # Internal attributes
            super().__setattr__(name, value)
            return

        all_attrs = self.get_all_attributes()
        if name not in all_attrs:
            raise AttributeError(f"Cannot set unknown attribute '{name}'")
            
        attr_def = all_attrs[name]
        if not self._validate_type(value, attr_def.type):
            raise TypeError(f"Attribute '{name}' must be of type {attr_def.type}")
        self._attrs[name] = value

    def get_attribute(self, name: str, default: Any = None) -> Any:
        """Get attribute value with optional default"""
        return self._attributes.get(name, default)

    def set_attribute(self, name: str, value: Any) -> None:
        """Set attribute value with type checking"""
        setattr(self, name, value)

    @property
    def name(self) -> str:
        """Entity name"""
        return self._name
