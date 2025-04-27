import json
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from decimal import Decimal

from utms.core.time.decimal import DecimalTimeStamp, DecimalTimeLength, DecimalTimeRange
from utms.core.logger import get_logger
from utms.utils import hy_to_python
from utms.utms_types import HyExpression

logger = get_logger()

class FieldType(Enum):
    """Enum representing the supported field types for entity attributes."""
    
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    DECIMAL = "decimal"
    BOOLEAN = "boolean"
    TIMESTAMP = "timestamp"
    TIMELENGTH = "timelength"
    TIMERANGE = "timerange"
    LIST = "list"
    DICT = "dict"
    CODE = "code"
    ENUM = "enum"
    
    @classmethod
    def from_string(cls, type_str: str) -> "FieldType":
        """Convert a string to a FieldType enum value."""
        try:
            return cls(type_str.lower())
        except ValueError:
            return cls.STRING  # Default to string for unknown types
    
    def __str__(self) -> str:
        """Return the string representation of the field type."""
        return self.value


class TypedValue:
    """Class to store a value with its type information."""
    
    def __init__(
        self, 
        value: Any, 
        field_type: Union[FieldType, str],
        item_type: Optional[Union[FieldType, str]] = None,  # For collections
        is_dynamic: bool = False,
        original: Optional[str] = None,
        enum_choices: Optional[List[Any]] = None  # Add enum_choices parameter
    ):
        # Convert string type to enum if needed
        if isinstance(field_type, str):
            field_type = FieldType.from_string(field_type)
            
        if isinstance(item_type, str) and item_type is not None:
            item_type = FieldType.from_string(item_type)
            
        self.field_type = field_type
        self.item_type = item_type
        self.is_dynamic = is_dynamic
        self.original = original
        self.enum_choices = enum_choices or []  # Store the enum choices
        
        # Store the raw value before conversion
        self._raw_value = value
        
        # Convert and store the value according to its type
        self._value = self._convert_value(value)
    
    @property
    def value(self) -> Any:
        """Get the typed value."""
        return self._value
    
    @value.setter
    def value(self, new_value: Any) -> None:
        """Set and convert the value based on the field type."""
        self._raw_value = new_value
        self._value = self._convert_value(new_value)


    def __int__(self):
        """Allow direct conversion to int."""
        if self.field_type == FieldType.INTEGER:
            return int(self.value)
        elif self.field_type == FieldType.DECIMAL or self.field_type == FieldType.FLOAT:
            return int(float(self.value))
        elif self.field_type == FieldType.BOOLEAN:
            return 1 if self.value else 0
        elif self.field_type == FieldType.STRING:
            try:
                return int(self.value)
            except (ValueError, TypeError):
                raise TypeError(f"Cannot convert string '{self.value}' to int")
        else:
            raise TypeError(f"Cannot convert {self.field_type} to int")

    def __float__(self):
        """Allow direct conversion to float."""
        if self.field_type == FieldType.INTEGER or self.field_type == FieldType.DECIMAL or self.field_type == FieldType.FLOAT:
            return float(self.value)
        elif self.field_type == FieldType.BOOLEAN:
            return 1.0 if self.value else 0.0
        elif self.field_type == FieldType.STRING:
            try:
                return float(self.value)
            except (ValueError, TypeError):
                raise TypeError(f"Cannot convert string '{self.value}' to float")
        else:
            raise TypeError(f"Cannot convert {self.field_type} to float")

    def __bool__(self):
        """Allow direct conversion to bool."""
        if self.field_type == FieldType.BOOLEAN:
            return self.value
        elif self.field_type == FieldType.INTEGER or self.field_type == FieldType.DECIMAL or self.field_type == FieldType.FLOAT:
            return bool(self.value)
        elif self.field_type == FieldType.STRING:
            return bool(self.value) and self.value.lower() not in ('false', 'no', '0', 'f', 'n', '')
        elif self.value is None:
            return False
        else:
            return bool(self.value)

    def __eq__(self, other):
        """Equality comparison."""
        if isinstance(other, TypedValue):
            return self.value == other.value
        return self.value == other

    def __ne__(self, other):
        """Inequality comparison."""
        return not self.__eq__(other)

    def __lt__(self, other):
        """Less than comparison."""
        if isinstance(other, TypedValue):
            return self.value < other.value
        return self.value < other

    def __le__(self, other):
        """Less than or equal comparison."""
        if isinstance(other, TypedValue):
            return self.value <= other.value
        return self.value <= other

    def __gt__(self, other):
        """Greater than comparison."""
        if isinstance(other, TypedValue):
            return self.value > other.value
        return self.value > other

    def __ge__(self, other):
        """Greater than or equal comparison."""
        if isinstance(other, TypedValue):
            return self.value >= other.value
        return self.value >= other

    def __add__(self, other):
        """Addition operator."""
        if isinstance(other, TypedValue):
            return self.value + other.value
        return self.value + other

    def __radd__(self, other):
        """Reverse addition operator."""
        return other + self.value

    def __sub__(self, other):
        """Subtraction operator."""
        if isinstance(other, TypedValue):
            return self.value - other.value
        return self.value - other

    def __rsub__(self, other):
        """Reverse subtraction operator."""
        return other - self.value

    def __mul__(self, other):
        """Multiplication operator."""
        if isinstance(other, TypedValue):
            return self.value * other.value
        return self.value * other

    def __rmul__(self, other):
        """Reverse multiplication operator."""
        return other * self.value

    def __truediv__(self, other):
        """Division operator."""
        if isinstance(other, TypedValue):
            return self.value / other.value
        return self.value / other

    def __rtruediv__(self, other):
        """Reverse division operator."""
        return other / self.value

    def __iter__(self):
        """Iterator support for list-like types."""
        if isinstance(self.value, (list, tuple, dict)):
            return iter(self.value)
        raise TypeError(f"'{self.field_type}' object is not iterable")

    def __getitem__(self, key):
        """Index/key access for list/dict types."""
        if isinstance(self.value, (list, tuple, dict)):
            return self.value[key]
        raise TypeError(f"'{self.field_type}' object is not subscriptable")

    def __len__(self):
        """Length support for list-like types."""
        if isinstance(self.value, (list, tuple, dict, str)):
            return len(self.value)
        raise TypeError(f"Object of type '{self.field_type}' has no len()")

    def __contains__(self, item):
        """Container support (in operator)."""
        if isinstance(self.value, (list, tuple, dict, str)):
            return item in self.value
        raise TypeError(f"'{self.field_type}' object is not a container")

    def __hash__(self):
        """Hash support for using in sets and as dictionary keys."""
        try:
            return hash((self.field_type, self.value))
        except TypeError:
            # Fall back for unhashable types
            return id(self)


    
    def _convert_value(self, value: Any) -> Any:
        """Convert a value to the correct type."""
        if value is None:
            return None
            
        try:
            if self.field_type == FieldType.STRING:
                return str(value)
            elif self.field_type == FieldType.INTEGER:
                if isinstance(value, bool):  # Handle boolean special case
                    return 1 if value else 0
                return int(value)
            elif self.field_type == FieldType.FLOAT:
                return float(value)
            elif self.field_type == FieldType.DECIMAL:
                return Decimal(str(value))
            elif self.field_type == FieldType.BOOLEAN:
                if isinstance(value, str):
                    return value.lower() in ('true', 'yes', '1', 't', 'y')
                return bool(value)
            elif self.field_type == FieldType.TIMESTAMP:
                if isinstance(value, DecimalTimeStamp):
                    return value
                return DecimalTimeStamp(value)
            elif self.field_type == FieldType.TIMELENGTH:
                if isinstance(value, DecimalTimeLength):
                    return value
                return DecimalTimeLength(value)
            elif self.field_type == FieldType.TIMERANGE:
                # TimeRange requires special handling
                
                if isinstance(value, DecimalTimeRange):
                    return value
                    
                if isinstance(value, dict) and 'start' in value and 'duration' in value:
                    start = value['start']
                    if not isinstance(start, DecimalTimeStamp):
                        start = DecimalTimeStamp(start)
                        
                    duration = value['duration']
                    if not isinstance(duration, DecimalTimeLength):
                        duration = DecimalTimeLength(duration)
                        
                    return DecimalTimeRange(start, duration)
                    
                # Default empty range
                return DecimalTimeRange(DecimalTimeStamp(0), DecimalTimeLength(0))
            elif self.field_type == FieldType.LIST:
                # Convert to list if not already
                if not isinstance(value, list):
                    if isinstance(value, str):
                        # Try to parse as JSON
                        try:
                            value = json.loads(value)
                            if not isinstance(value, list):
                                value = [value]
                        except:
                            value = [value]
                    else:
                        value = [value]
                
                # Convert list items if item_type is specified
                if self.item_type:
                    return [TypedValue(item, self.item_type).value for item in value]
                return value
            elif self.field_type == FieldType.DICT:
                # Convert to dict if not already
                if not isinstance(value, dict):
                    if isinstance(value, str):
                        # Try to parse as JSON
                        try:
                            value = json.loads(value)
                            if not isinstance(value, dict):
                                value = {"value": value}
                        except:
                            value = {"value": value}
                    else:
                        value = {"value": value}
                
                # Convert dict values if item_type is specified
                if self.item_type:
                    return {k: TypedValue(v, self.item_type).value for k, v in value.items()}
                return value
            elif self.field_type == FieldType.ENUM:
                if not self.enum_choices:
                    return None

                value_str = str(value).lower() if value is not None else ""
                for choice in self.enum_choices:
                    if str(choice).lower() == value_str:
                        return choice
                return self.enum_choices[0]

            elif self.field_type == FieldType.CODE:
                # Store code as string, it will be evaluated separately
                return value
            else:
                # Unknown type, return as is
                return value
        except Exception as e:
            # Log the error and return None for conversion errors
            logger.error(f"Error converting value {value} to type {self.field_type}: {e}")
            return None
    
    def serialize(self) -> Dict[str, Any]:
        """Convert to a serializable dictionary."""
        result = {
            "type": str(self.field_type),
            "value": self._serialize_value()
        }
        
        if self.item_type:
            result["item_type"] = str(self.item_type)
            
        if self.is_dynamic:
            result["is_dynamic"] = True
            
        if self.original:
            result["original"] = self.original

        if self.field_type == FieldType.ENUM and self.enum_choices:
            result["enum_choices"] = self.enum_choices
            
        return result
    
    def _serialize_value(self) -> Any:
        """Convert the value to a serializable format."""
        if self.value is None:
            return None
            
        # Handle special types
        if self.field_type == FieldType.TIMESTAMP:
            if isinstance(self.value, DecimalTimeStamp):
                return float(self.value)
            return self.value
            
        elif self.field_type == FieldType.TIMELENGTH:
            if isinstance(self.value, DecimalTimeLength):
                return float(self.value)
            return self.value
            
        elif self.field_type == FieldType.TIMERANGE:
            if isinstance(self.value, DecimalTimeRange):
                return {
                    "start": float(self.value.start),
                    "duration": float(self.value.duration)
                }
            return self.value
            
        elif self.field_type == FieldType.DECIMAL:
            if isinstance(self.value, Decimal):
                return str(self.value)
            return self.value
            
        elif self.field_type == FieldType.LIST:
            # Recursively serialize list items if they're TypedValue objects
            if isinstance(self.value, list):
                return [
                    item.serialize() if isinstance(item, TypedValue) else item
                    for item in self.value
                ]
            return self.value
            
        elif self.field_type == FieldType.DICT:
            # Recursively serialize dict values if they're TypedValue objects
            if isinstance(self.value, dict):
                return {
                    k: v.serialize() if isinstance(v, TypedValue) else v
                    for k, v in self.value.items()
                }
            return self.value
            
        else:
            return self.value
    
    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> "TypedValue":
        """Create a TypedValue from a serialized dictionary."""
        if not isinstance(data, dict):
            # Handle primitive values
            return cls(data, FieldType.STRING)
            
        field_type = data.get("type", FieldType.STRING)
        value = data.get("value")
        item_type = data.get("item_type")
        is_dynamic = data.get("is_dynamic", False)
        original = data.get("original")
        enum_choices = data.get("enum_choices", [])
        
        # Handle special deserialization for collections
        if field_type == FieldType.LIST and isinstance(value, list) and item_type:
            # Check if items are serialized TypedValues
            if value and isinstance(value[0], dict) and "type" in value[0]:
                value = [cls.deserialize(item) for item in value]
        
        if field_type == FieldType.DICT and isinstance(value, dict) and item_type:
            # Check if values are serialized TypedValues
            for k, v in value.items():
                if isinstance(v, dict) and "type" in v:
                    value[k] = cls.deserialize(v)
        
        return cls(
            value=value,
            field_type=field_type,
            item_type=item_type,
            is_dynamic=is_dynamic,
            original=original,
            enum_choices=enum_choices
        )
# utms/utms_types/field/types.py
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from decimal import Decimal

from utms.utms_types.base.protocols import TimeStamp, TimeLength, TimeRange


class FieldType(Enum):
    """Enum representing the supported field types for entity attributes."""
    
    STRING = "string"
    INTEGER = "integer"
    DECIMAL = "decimal"
    BOOLEAN = "boolean"
    TIMESTAMP = "timestamp"
    TIMELENGTH = "timelength"
    TIMERANGE = "timerange"
    LIST = "list"
    DICT = "dict"
    CODE = "code"  # For Hy expressions
    ENUM = "enum"  # For fields with a predefined set of values
    
    @classmethod
    def from_string(cls, type_str: str) -> "FieldType":
        """Convert a string to a FieldType enum value."""
        try:
            return cls(type_str.lower())
        except ValueError:
            return cls.STRING  # Default to string for unknown types
    
    def __str__(self) -> str:
        """Return the string representation of the field type."""
        return self.value


class TypedValue:
    """Class to store a value with its type information."""
    
    def __init__(
        self, 
        value: Any, 
        field_type: Union[FieldType, str],
        item_type: Optional[Union[FieldType, str]] = None,  # For collections
        is_dynamic: bool = False,
        original: Optional[str] = None,
        enum_choices: Optional[List[Any]] = None  # For ENUM type
    ):
        # Convert string type to enum if needed
        if isinstance(field_type, str):
            field_type = FieldType.from_string(field_type)
            
        if isinstance(item_type, str) and item_type is not None:
            item_type = FieldType.from_string(item_type)
            
        self.field_type = field_type
        self.item_type = item_type
        self.is_dynamic = is_dynamic
        self.original = original
        self.enum_choices = enum_choices or []  # Store the enum choices
        
        # Store the raw value before conversion
        self._raw_value = value
        
        # Convert and store the value according to its type
        self._value = self._convert_value(value)
    
    @property
    def value(self) -> Any:
        """Get the typed value."""
        return self._value
    
    @value.setter
    def value(self, new_value: Any) -> None:
        """Set and convert the value based on the field type."""
        self._raw_value = new_value
        self._value = self._convert_value(new_value)
    
    def _convert_value(self, value: Any) -> Any:
        """Convert a value to the correct type."""
        if value is None:
            return None

        py_value = hy_to_python(value)
            
        try:
            if self.field_type == FieldType.STRING:
                return str(py_value)
                
            elif self.field_type == FieldType.INTEGER:
                if isinstance(py_value, bool):  # Handle boolean special case
                    return 1 if py_value else 0
                return int(py_value)
                
            elif self.field_type == FieldType.DECIMAL:
                if isinstance(py_value, Decimal):
                    return py_value
                return Decimal(str(py_value))
                
            elif self.field_type == FieldType.BOOLEAN:
                if isinstance(py_value, str):
                    return py_value.lower() in ('true', 'yes', '1', 't', 'y')
                return bool(py_value)
                
            elif self.field_type == FieldType.TIMESTAMP:
                if isinstance(py_value, DecimalTimeStamp):
                    return py_value
                return DecimalTimeStamp(py_value)
                
            elif self.field_type == FieldType.TIMELENGTH:
                if isinstance(py_value, DecimalTimeLength):
                    return py_value
                return DecimalTimeLength(py_value)
                
            elif self.field_type == FieldType.TIMERANGE:
                if isinstance(py_value, DecimalTimeRange):
                    return py_value
                    
                if isinstance(py_value, dict) and 'start' in py_value and 'duration' in py_value:
                    start = py_value['start']
                    if not isinstance(start, DecimalTimeStamp):
                        start = DecimalTimeStamp(start)
                        
                    duration = py_value['duration']
                    if not isinstance(duration, DecimalTimeLength):
                        duration = DecimalTimeLength(duration)
                        
                    return DecimalTimeRange(start, duration)
                    
                # Default empty range
                return DecimalTimeRange(DecimalTimeStamp(0), DecimalTimeLength(0))
                
            elif self.field_type == FieldType.ENUM:
                # Handle enum type
                if not self.enum_choices:
                    return None
                
                # Convert py_value to string for comparison
                py_value_str = str(py_value).lower() if py_value is not None else ""
                
                # Try to find an exact match first
                for choice in self.enum_choices:
                    if str(choice).lower() == py_value_str:
                        return choice
                
                # If no exact match, return the first choice
                return self.enum_choices[0]
                
            elif self.field_type == FieldType.LIST:
                # Convert to list if not already
                if not isinstance(py_value, list):
                    if isinstance(py_value, str):
                        # Try to parse as JSON
                        import json
                        try:
                            py_value = json.loads(py_value)
                            if not isinstance(py_value, list):
                                py_value = [py_value]
                        except:
                            py_value = [py_value]
                    else:
                        py_value = [py_value]
                
                # Convert list items if item_type is specified
                if self.item_type:
                    return [TypedValue(item, self.item_type).py_value for item in py_value]
                return py_value
                
            elif self.field_type == FieldType.DICT:
                # Convert to dict if not already
                if not isinstance(py_value, dict):
                    if isinstance(py_value, str):
                        # Try to parse as JSON
                        import json
                        try:
                            py_value = json.loads(py_value)
                            if not isinstance(py_value, dict):
                                py_value = {"value": py_value}
                        except:
                            py_value = {"value": py_value}
                    else:
                        py_value = {"value": py_value}
                
                # Convert dict values if item_type is specified
                if self.item_type:
                    return {k: TypedValue(v, self.item_type).value for k, v in py_value.items()}
                return py_value
                
            elif self.field_type == FieldType.CODE:
                # Store code as string, it will be evaluated separately
                return value
                
            else:
                # Unknown type, return as is
                return py_value
                
        except Exception as e:
            # Log the error and return None for conversion errors
            logger.error(f"Error converting value {py_value} to type {self.field_type}: {e}")
            return None
    
    def serialize(self) -> Dict[str, Any]:
        """Convert to a serializable dictionary."""
        result = {
            "type": str(self.field_type),
            "value": self._serialize_value()
        }
        
        if self.item_type:
            result["item_type"] = str(self.item_type)
            
        if self.is_dynamic:
            result["is_dynamic"] = True
            
        if self.original:
            result["original"] = self.original
            
        # Include enum choices for ENUM type
        if self.field_type == FieldType.ENUM and self.enum_choices:
            result["enum_choices"] = self.enum_choices
            
        return result
    
    def _serialize_value(self) -> Any:
        """Convert the value to a serializable format."""
        if self.value is None:
            return None
            
        # Handle special types
        if self.field_type == FieldType.TIMESTAMP:
            if isinstance(self.value, DecimalTimeStamp):
                return float(self.value)
            return self.value
            
        elif self.field_type == FieldType.TIMELENGTH:
            if isinstance(self.value, DecimalTimeLength):
                return float(self.value)
            return self.value
            
        elif self.field_type == FieldType.TIMERANGE:
            if isinstance(self.value, DecimalTimeRange):
                return {
                    "start": float(self.value.start),
                    "duration": float(self.value.duration)
                }
            return self.value
            
        elif self.field_type == FieldType.DECIMAL:
            if isinstance(self.value, Decimal):
                return str(self.value)
            return self.value
            
        elif self.field_type == FieldType.LIST:
            # Recursively serialize list items if they're TypedValue objects
            if isinstance(self.value, list):
                return [
                    item.serialize() if isinstance(item, TypedValue) else item
                    for item in self.value
                ]
            return self.value
            
        elif self.field_type == FieldType.DICT:
            # Recursively serialize dict values if they're TypedValue objects
            if isinstance(self.value, dict):
                return {
                    k: v.serialize() if isinstance(v, TypedValue) else v
                    for k, v in self.value.items()
                }
            return self.value
            
        else:
            return self.value
    
    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> "TypedValue":
        """Create a TypedValue from a serialized dictionary."""
        if not isinstance(data, dict):
            # Handle primitive values
            return cls(data, FieldType.STRING)
            
        field_type = data.get("type", FieldType.STRING)
        value = data.get("value")
        item_type = data.get("item_type")
        is_dynamic = data.get("is_dynamic", False)
        original = data.get("original")
        enum_choices = data.get("enum_choices", [])
        
        # Handle special deserialization for collections
        if field_type == FieldType.LIST.value and isinstance(value, list) and item_type:
            # Check if items are serialized TypedValues
            if value and isinstance(value[0], dict) and "type" in value[0]:
                value = [cls.deserialize(item) for item in value]
        
        if field_type == FieldType.DICT.value and isinstance(value, dict) and item_type:
            # Check if values are serialized TypedValues
            for k, v in value.items():
                if isinstance(v, dict) and "type" in v:
                    value[k] = cls.deserialize(v)
        
        return cls(
            value=value,
            field_type=field_type,
            item_type=item_type,
            is_dynamic=is_dynamic,
            original=original,
            enum_choices=enum_choices
        )
    
    def validate(self) -> bool:
        """Validate that the value matches the expected type."""
        if self.value is None:
            return True  # None is valid for any type
            
        try:
            if self.field_type == FieldType.STRING:
                return isinstance(self.value, str)
                
            elif self.field_type == FieldType.INTEGER:
                return isinstance(self.value, int) and not isinstance(self.value, bool)
                
            elif self.field_type == FieldType.DECIMAL:
                return isinstance(self.value, Decimal)
                
            elif self.field_type == FieldType.BOOLEAN:
                return isinstance(self.value, bool)
                
            elif self.field_type == FieldType.TIMESTAMP:
                return isinstance(self.value, DecimalTimeStamp)
                
            elif self.field_type == FieldType.TIMELENGTH:
                return isinstance(self.value, DecimalTimeLength)
                
            elif self.field_type == FieldType.TIMERANGE:
                return isinstance(self.value, DecimalTimeRange)
                
            elif self.field_type == FieldType.ENUM:
                return self.value in self.enum_choices
                
            elif self.field_type == FieldType.LIST:
                if not isinstance(self.value, list):
                    return False
                # Validate list items if item_type is specified
                if self.item_type:
                    return all(TypedValue(item, self.item_type).validate() for item in self.value)
                return True
                
            elif self.field_type == FieldType.DICT:
                if not isinstance(self.value, dict):
                    return False
                # Validate dict values if item_type is specified
                if self.item_type:
                    return all(TypedValue(v, self.item_type).validate() for v in self.value.values())
                return True
                
            elif self.field_type == FieldType.CODE:
                return isinstance(self.value, str)
                
            else:
                return True  # Unknown types are always valid
                
        except Exception:
            return False
    
    def __str__(self) -> str:
        """String representation of the typed value."""
        if self.is_dynamic and self.original:
            return f"{self.original} → {self.value}"
        return str(self.value)
    
    def __repr__(self) -> str:
        """Detailed representation of the typed value."""
        type_str = str(self.field_type)
        if self.item_type:
            type_str += f"[{self.item_type}]"
        if self.enum_choices:
            type_str += f"({self.enum_choices})"
        return f"TypedValue({self.value}, {type_str})"


# Utility functions

def infer_type(value: Any) -> FieldType:
    """Infer the field type from a value."""
    if value is None:
        return FieldType.STRING
    
    if isinstance(value, bool):
        return FieldType.BOOLEAN
    
    if isinstance(value, int):
        return FieldType.INTEGER
    
    if isinstance(value, float) or isinstance(value, Decimal):
        return FieldType.DECIMAL
    
    if isinstance(value, list):
        return FieldType.LIST
    
    if isinstance(value, dict):
        return FieldType.DICT
    
    if isinstance(value, DecimalTimeStamp):
        return FieldType.TIMESTAMP
    
    if isinstance(value, DecimalTimeLength):
        return FieldType.TIMELENGTH
    
    if isinstance(value, DecimalTimeRange):
        return FieldType.TIMERANGE
    
    if isinstance(value, str) and value.strip().startswith('(') and value.strip().endswith(')'):
        return FieldType.CODE

    if isinstance(value, HyExpression):
        return FieldType.CODE
    
    # Default to string
    return FieldType.STRING


def infer_item_type(values: List[Any]) -> Optional[FieldType]:
    """Infer the common item type for a list of values."""
    if not values:
        return None
        
    # Get the type of the first item
    first_type = infer_type(values[0])
    
    # Check if all items have the same type
    for value in values[1:]:
        if infer_type(value) != first_type:
            # If mixed types, return None
            return None
            
    return first_type


def convert_value(value: Any, target_type: Union[FieldType, str], **kwargs) -> Any:
    """Convert a value to the target type."""
    return TypedValue(value, target_type, **kwargs).value


def typed_value_from_json(json_data: Dict[str, Any]) -> TypedValue:
    """Create a TypedValue from JSON data."""
    return TypedValue.deserialize(json_data)


def json_from_typed_value(typed_value: TypedValue) -> Dict[str, Any]:
    """Convert a TypedValue to JSON data."""
    return typed_value.serialize()


def is_valid_for_type(value: Any, field_type: Union[FieldType, str], **kwargs) -> bool:
    """Check if a value is valid for the specified type."""
    typed_value = TypedValue(value, field_type, **kwargs)
    return typed_value.validate()
