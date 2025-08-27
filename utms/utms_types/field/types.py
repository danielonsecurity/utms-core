from datetime import datetime
import json
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import hy
from hy.models import Expression, Symbol

from utms.core.hy.converter import converter
from utms.core.logger import get_logger
from utms.core.time.decimal import DecimalTimeLength, DecimalTimeRange, DecimalTimeStamp
from utms.core.hy.converter import converter, py_list_to_hy_expression

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
    DATETIME = "datetime"
    LIST = "list"
    DICT = "dict"
    CODE = "code"
    ACTION = "action"
    ENUM = "enum"
    ENTITY_REFERENCE = "entity_reference"

    @classmethod
    def from_string(cls, type_str: str) -> "FieldType":
        """Convert a string to a FieldType enum value."""
        try:
            return cls(type_str.lower())
        except ValueError:
            logger.warning(
                f"Unknown FieldType string '{type_str}' encountered. Defaulting to STRING."
            )
            return cls.STRING  

    def __str__(self) -> str:
        """Return the string representation of the field type."""
        return self.value


class TypedValue:
    def __init__(
        self,
        value: Any,
        field_type: Union[FieldType, str],
        item_type: Optional[Union[FieldType, str]] = None,
        is_dynamic: bool = False,
        original: Optional[str] = None,
        enum_choices: Optional[List[Any]] = None,
        item_schema_type: Optional[str] = None,
        referenced_entity_type: Optional[str] = None,
        referenced_entity_category: Optional[str] = None,
    ):
        """
        Initializes a TypedValue, enforcing a clean two-step process:
        1. Normalize the input from any format into a rich Python object.
        2. Coerce that Python object into the specified FieldType.
        """
        if isinstance(field_type, str): self.field_type = FieldType.from_string(field_type)
        else: self.field_type = field_type

        if item_type and isinstance(item_type, str): self.item_type = FieldType.from_string(item_type)
        else: self.item_type = item_type

        self.is_dynamic = is_dynamic
        self.enum_choices = enum_choices or []
        self.item_schema_type = item_schema_type
        self.referenced_entity_type = referenced_entity_type
        self.referenced_entity_category = referenced_entity_category

        if self.is_dynamic or self.field_type in (FieldType.CODE, FieldType.ACTION):
            self._value = value
        else:
            py_value = converter.model_to_py(value)
            self._value = self._coerce(py_value)

        if original is not None: self.original = original
        else: self.original = self._get_original_string_from_input(value)

    def _get_original_string_from_input(self, original_input: Any) -> Optional[str]:
        """Determines the 'original' string representation for dynamic values."""
        if self.is_dynamic:
            if isinstance(original_input, hy.models.Object):
                return converter.model_to_string(original_input)
            if isinstance(original_input, str):
                return original_input
        return None
    
    def _coerce(self, py_value: Any) -> Any:
        """
        Takes a clean Python object and coerces it to the specific FieldType.
        This method is the dedicated "Type Enforcer".
        """
        if self.is_dynamic:
            return py_value

        if py_value is None:
            return None

        try:
            if self.field_type == FieldType.STRING: return str(py_value)
            elif self.field_type == FieldType.INTEGER: return int(py_value)
            elif self.field_type == FieldType.DECIMAL: return Decimal(str(py_value))
            elif self.field_type == FieldType.BOOLEAN:
                if isinstance(py_value, str): return py_value.lower() in ("true", "yes", "1", "t", "y")
                return bool(py_value)
            elif self.field_type == FieldType.TIMESTAMP: return DecimalTimeStamp(py_value)
            elif self.field_type == FieldType.TIMELENGTH: return DecimalTimeLength(py_value)
            elif self.field_type == FieldType.TIMERANGE:
                if isinstance(py_value, dict): return DecimalTimeRange(py_value['start'], py_value['duration'])
                return DecimalTimeRange(py_value)
            elif self.field_type == FieldType.DATETIME:
                if isinstance(py_value, datetime): return py_value
                if isinstance(py_value, str): return datetime.fromisoformat(py_value.replace("Z", "+00:00"))
                raise TypeError(f"Cannot coerce {type(py_value)} to datetime")
            elif self.field_type == FieldType.LIST:
                if isinstance(py_value, list): return py_value
                return [py_value]
            elif self.field_type == FieldType.DICT:
                if isinstance(py_value, dict): return py_value
                return {'value': py_value}
            elif self.field_type == FieldType.ENUM:
                if self.enum_choices and py_value in self.enum_choices: return py_value
                return self.enum_choices[0] if self.enum_choices else None
            elif self.field_type in [FieldType.CODE, FieldType.ACTION, FieldType.ENTITY_REFERENCE]:
                return py_value
            else:
                logger.warning(f"Unhandled FieldType '{self.field_type}' in _coerce. Returning value as is.")
                return py_value

        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"Could not coerce value '{py_value}' (type: {type(py_value)}) to {self.field_type}: {e}")
            return None

    @property
    def value(self) -> Any:
        return self._value

    @value.setter
    def value(self, new_value: Any) -> None:
        """Setter that enforces the clean conversion pipeline when the value is changed."""
        py_value = converter.model_to_py(new_value)
        self._value = self._coerce(py_value)

    def serialize(self) -> Dict[str, Any]:
        result = {
            "type": str(self.field_type),
            "value": self._serialize_value(),
        }

        if self.item_type:
            result["item_type"] = str(self.item_type)
        if self.is_dynamic:
            result["is_dynamic"] = True
        if self.original:
            result["original"] = self.original
        if self.field_type == FieldType.ENUM and self.enum_choices:
            result["enum_choices"] = self.enum_choices

        
        if self.item_schema_type:
            result["item_schema_type"] = self.item_schema_type
        if self.referenced_entity_type:
            result["referenced_entity_type"] = self.referenced_entity_type
        if self.referenced_entity_category:
            result["referenced_entity_category"] = self.referenced_entity_category

        return result

    def serialize_for_persistence(self) -> str:
        """
        Serializes the internal value into an idempotent and syntactically correct Hy string.
        """
        if self.is_dynamic and self.original:
            return self.original

        value = self.value
        if value is None:
            return "None"

        if self.field_type in (FieldType.CODE, FieldType.ACTION):
            if isinstance(self.value, hy.models.Object):
                return converter.model_to_string(self.value)
            if isinstance(self.value, list):
                try:
                    hy_expr = py_list_to_hy_expression(self.value)
                    return converter.model_to_string(hy_expr)
                except Exception as e:
                    logger.error(f"Failed to convert CODE list to expression: {e}. Falling back.")
        return converter.py_to_string(self.value)

    def _serialize_value(self) -> Any:
        """Convert the value to a serializable format."""
        val_to_serialize = self.value

        if val_to_serialize is None:
            return None

        if self.field_type in (FieldType.CODE, FieldType.ACTION) and isinstance(val_to_serialize, (Expression, Symbol)):
            return converter.model_to_string(val_to_serialize)

        if self.field_type == FieldType.LIST and self.item_schema_type:
            if not isinstance(val_to_serialize, list):
                return val_to_serialize 
            def deep_serialize_hy(data: Any) -> Any:
                if isinstance(data, (Expression, Symbol)):
                    return converter.model_to_string(data)
                if isinstance(data, list):
                    return [deep_serialize_hy(item) for item in data]
                if isinstance(data, dict):
                    return {str(k): deep_serialize_hy(v) for k, v in data.items()}
                if isinstance(data, hy.models.Object):
                    python_equivalent = converter.model_to_py(data, raw=True)
                    return deep_serialize_hy(python_equivalent)
                return data
            return deep_serialize_hy(val_to_serialize)

        if self.field_type == FieldType.DATETIME:
            if isinstance(val_to_serialize, datetime):
                return val_to_serialize.isoformat()
            if isinstance(val_to_serialize, DecimalTimeStamp):
                return float(val_to_serialize)
            return str(val_to_serialize)

        if self.field_type == FieldType.ENTITY_REFERENCE:
            return val_to_serialize

        if self.field_type == FieldType.TIMESTAMP:
            return (
                float(val_to_serialize)
                if isinstance(val_to_serialize, DecimalTimeStamp)
                else val_to_serialize
            )
        elif self.field_type == FieldType.TIMELENGTH:
            return (
                float(val_to_serialize)
                if isinstance(val_to_serialize, DecimalTimeLength)
                else val_to_serialize
            )
        elif self.field_type == FieldType.TIMERANGE:
            if isinstance(val_to_serialize, DecimalTimeRange):
                return {
                    "start": float(val_to_serialize.start),
                    "duration": float(val_to_serialize.duration),
                }
            return val_to_serialize
        elif self.field_type == FieldType.DECIMAL:
            return (
                str(val_to_serialize) if isinstance(val_to_serialize, Decimal) else val_to_serialize
            )

        elif self.field_type == FieldType.LIST:  
            if isinstance(val_to_serialize, list):
                
                return val_to_serialize
            return val_to_serialize

        elif self.field_type == FieldType.DICT:  
            if isinstance(val_to_serialize, dict):
                
                return val_to_serialize
            return val_to_serialize

        else:  
            return val_to_serialize

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> "TypedValue":
        """Create a TypedValue from a serialized dictionary."""
        if not isinstance(data, dict):
            logger.warning(
                f"Attempting to deserialize non-dict data: {data}. Assuming STRING type."
            )
            return cls(data, FieldType.STRING)

        field_type_str = data.get("type", FieldType.STRING.value)  
        value = data.get("value")
        item_type_str = data.get("item_type")
        is_dynamic = data.get("is_dynamic", False)
        original = data.get("original")
        enum_choices = data.get("enum_choices", [])

        
        item_schema_type = data.get("item_schema_type")
        referenced_entity_type = data.get("referenced_entity_type")
        referenced_entity_category = data.get("referenced_entity_category")

        field_type_enum = FieldType.from_string(field_type_str)
        item_type_enum = FieldType.from_string(item_type_str) if item_type_str else None

        if field_type_enum == FieldType.CODE and isinstance(value, str) and value.strip().startswith('('):
            try:
                parsed_value = hy.read(value)
                if isinstance(parsed_value, (hy.models.Expression, hy.models.Symbol)):
                    value = parsed_value
                else:
                    logger.warning(
                        f"Deserializing CODE field, but parsed value is not a Hy Expression/Symbol: '{value}'. Using as string."
                    )
            except Exception as e:
                logger.error(
                    f"Error using hy.read on CODE field value '{value}': {e}. Using as string."
                )

        if field_type_enum == FieldType.LIST and item_schema_type and isinstance(value, list):
            processed_value_list = []
            for item_str in value:
                if isinstance(item_str, str) and item_str.strip().startswith("("):
                    try:
                        
                        parsed_item = next(iter(hy.read_many(item_str)), None)
                        if parsed_item is not None:
                            processed_value_list.append(parsed_item)
                        else:
                            logger.warning(
                                f"Failed to parse list item S-expression string: '{item_str}'. Appending as string."
                            )
                            processed_value_list.append(item_str)  
                    except Exception as e:
                        logger.error(
                            f"Error hy.read_many on list item '{item_str}': {e}. Appending as string."
                        )
                        processed_value_list.append(item_str)  
                else:
                    processed_value_list.append(item_str)  
            value = processed_value_list

        if (
            field_type_enum == FieldType.ENTITY_REFERENCE
            and is_dynamic
            and isinstance(value, str)
            and value.strip().startswith("(")
        ):
            try:
                parsed_value = next(iter(hy.read_many(value)), None)
                if parsed_value is not None:
                    value = parsed_value  
                else:
                    logger.warning(
                        f"Failed to parse entity_reference S-expression string: '{value}'. Using as string."
                    )
            except Exception as e:
                logger.error(
                    f"Error hy.read_many on entity_reference value '{value}': {e}. Using as string."
                )

        
        return cls(
            value=value,  
            field_type=field_type_enum,
            item_type=item_type_enum,
            is_dynamic=is_dynamic,
            original=original,
            enum_choices=enum_choices,
            item_schema_type=item_schema_type,
            referenced_entity_type=referenced_entity_type,
            referenced_entity_category=referenced_entity_category,
        )

    def validate(self) -> bool:
        """Validate that the value matches the expected type."""
        if self.value is None:
            return True  

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
                if self.item_schema_type:
                    return True
                if self.item_type:
                    return all(TypedValue(item, self.item_type).validate() for item in self.value)
                return True
            elif self.field_type == FieldType.DICT:
                if not isinstance(self.value, dict):
                    return False
                if self.item_type:
                    return all(
                        TypedValue(v, self.item_type).validate() for v in self.value.values()
                    )
                return True
            elif self.field_type == FieldType.CODE:
                return True
            elif self.field_type == FieldType.ENTITY_REFERENCE:
                return isinstance(self.value, (str, hy.models.Expression, dict))

            else:
                return True

        except Exception:
            return False

    def __str__(self) -> str:
        if self.is_dynamic and self.original:
            val_str = (
                hy.repr(self.value) if isinstance(self.value, hy.models.Object) else str(self.value)
            )
            return f"{self.original} → {val_str}"

        return hy.repr(self.value) if isinstance(self.value, hy.models.Object) else str(self.value)

    def __repr__(self) -> str:
        type_str = str(self.field_type)
        if self.item_type:
            type_str += f"[{self.item_type}]"
        if self.item_schema_type:
            type_str += f"<schema:{self.item_schema_type}>"
        if self.enum_choices:
            type_str += f"({self.enum_choices})"
        if self.referenced_entity_type:
            type_str += f"->{self.referenced_entity_type}"
        if self.referenced_entity_category:
            type_str += f":{self.referenced_entity_category}"

        val_repr = (
            hy.repr(self._value) if isinstance(self._value, hy.models.Object) else repr(self._value)
        )
        return f"TypedValue({val_repr}, {type_str})"


def infer_type(value: Any) -> FieldType:
    if value is None:
        return FieldType.STRING

    if isinstance(value, Expression) and len(value) > 0:
        first_symbol_str = str(value[0]).lower()
        if first_symbol_str in ("datetime", "timestamp", "timelength", "timerange"):
            return FieldType.DATETIME
        if first_symbol_str == "entity-ref":
            return FieldType.ENTITY_REFERENCE

    if isinstance(value, datetime):
        return FieldType.DATETIME

    if isinstance(value, DecimalTimeStamp):
        return FieldType.TIMESTAMP
    if isinstance(value, DecimalTimeLength):
        return FieldType.TIMELENGTH
    if isinstance(value, DecimalTimeRange):
        return FieldType.TIMERANGE

    if isinstance(value, bool):
        return FieldType.BOOLEAN
    if isinstance(value, int):
        return FieldType.INTEGER
    if isinstance(value, float) or isinstance(value, Decimal):
        return FieldType.DECIMAL
    if isinstance(value, list) or isinstance(value, hy.models.List):
        return FieldType.LIST  
    if isinstance(value, dict) or isinstance(value, hy.models.Dict):
        return FieldType.DICT  

    if isinstance(value, Expression):
        return FieldType.CODE

    if isinstance(value, str) and value.strip().startswith("(") and value.strip().endswith(")"):
        try:
            parsed_hy = hy.read(value)
            if isinstance(parsed_hy, (Expression, Symbol)):
                return FieldType.CODE
        except Exception:
            pass  

    
    return FieldType.STRING


def infer_item_type(values: List[Any]) -> Optional[FieldType]:
    """Infer the common item type for a list of values."""
    if not values:
        return None

    
    first_type = infer_type(values[0])

    
    for value in values[1:]:
        if infer_type(value) != first_type:
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
