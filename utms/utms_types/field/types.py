import json
import hy
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from decimal import Decimal

from utms.core.time.decimal import DecimalTimeStamp, DecimalTimeLength, DecimalTimeRange
from utms.core.logger import get_logger
from utms.utils import hy_to_python
from utms.utms_types import HyExpression
from utms.core.hy.utils import format_value

logger = get_logger()

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
                # py_value here should already be a Python list from hy_to_python(value)
                # if value was a HyList/HyExpression.
                # If value was a string like "['a','b']", hy_to_python might not parse it as list.
                # The original code had JSON parsing here, which might be needed if strings can represent lists.
                current_list_val = py_value
                if not isinstance(current_list_val, list):
                    if isinstance(current_list_val, str):
                        try:
                            loaded_json = json.loads(current_list_val)
                            if isinstance(loaded_json, list): current_list_val = loaded_json
                            else: current_list_val = [loaded_json] # Wrap non-list JSON into a list
                        except json.JSONDecodeError:
                            current_list_val = [current_list_val] # Treat as a single-item list
                    else:
                        current_list_val = [current_list_val] # Wrap non-list, non-string into a list
                
                if self.item_type and current_list_val: # Ensure current_list_val is not empty
                    # Recursively create TypedValue for items to ensure they are converted.
                    # The .value access then gets the Python native type.
                    return [TypedValue(item, self.item_type).value for item in current_list_val]
                return current_list_val # Return list of Python natives
                
            elif self.field_type == FieldType.DICT:
                # py_value here should already be a Python dict from hy_to_python(value)
                # if value was a HyDict.
                current_dict_val = py_value
                if not isinstance(current_dict_val, dict):
                    if isinstance(current_dict_val, str):
                        try:
                            loaded_json = json.loads(current_dict_val)
                            if isinstance(loaded_json, dict): current_dict_val = loaded_json
                            else: current_dict_val = {"value": loaded_json}
                        except json.JSONDecodeError:
                             current_dict_val = {"value": current_dict_val} # Wrap into a dict
                    else:
                        current_dict_val = {"value": current_dict_val} # Wrap non-dict, non-string into a dict

                if self.item_type and current_dict_val:
                    return {k: TypedValue(v, self.item_type).value for k, v in current_dict_val.items()}
                return current_dict_val # Return dict of Python natives
                
            elif self.field_type == FieldType.CODE:
                # For dynamic CODE fields:
                #   'value' passed to __init__ by the loader IS the resolved Python value.
                #   'py_value' here is that resolved Python value. Correctly return it.
                # For static CODE fields:
                #   'value' passed to __init__ by the plugin is the raw HyObject (e.g. HyString, HyDict).
                #   'py_value' here is the result of hy_to_python(rawHyObject).
                #   This py_value (e.g. Python string, Python dict) should be stored.
                return py_value # This now correctly stores the Python native version
                
            else: # Unknown FieldType
                # py_value is the hy_to_python version. This is the safest to return.
                logger.warning(f"Unknown FieldType '{self.field_type}' encountered for value '{value}'. "
                               f"Storing hy_to_python converted value: '{py_value}'.")
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
    
    def serialize_for_persistence(self) -> str:
        """
        Serialize the value into a string suitable for persistence in a .hy file.
        Follows the Chronoiconicity principle (code=data).
        """
        if self.is_dynamic and self.original:
            return self.original

        elif self.field_type == FieldType.CODE:
            if isinstance(self.value, str):
                if self.value.strip().startswith('(') and self.value.strip().endswith(')'):
                     return self.value
                else:
                     return hy.repr(self.value)
            else:
                 return format_value(self.value)
        return format_value(self.value)


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
    
    if isinstance(value, hy.models.List):
        return FieldType.LIST
    if isinstance(value, hy.models.Dict):
        return FieldType.DICT

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
