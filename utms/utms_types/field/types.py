import datetime
import json
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import hy
from hy.models import Expression, Symbol

from utms.core.hy.utils import format_value
from utms.core.logger import get_logger
from utms.core.time.decimal import DecimalTimeLength, DecimalTimeRange, DecimalTimeStamp
from utms.utils import hy_to_python

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
    CODE = "code"  # For Hy expressions
    ENUM = "enum"  # For fields with a predefined set of values
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
            return cls.STRING  # Default to string for unknown types

    def __str__(self) -> str:
        """Return the string representation of the field type."""
        return self.value


class TypedValue:
    def __init__(
        self,
        value: Any,
        field_type: Union[FieldType, str],
        # Existing parameters
        item_type: Optional[Union[FieldType, str]] = None,
        is_dynamic: bool = False,
        original: Optional[str] = None,
        enum_choices: Optional[List[Any]] = None,
        # New parameters for complex types and references
        item_schema_type: Optional[str] = None,  # For LIST of complex objects
        # item_schema: Optional[Dict[str, Any]] = None, # Deferred: for inline complex object schemas
        referenced_entity_type: Optional[str] = None,  # For ENTITY_REFERENCE
        referenced_entity_category: Optional[
            str
        ] = None,  # For ENTITY_REFERENCE (optional constraint)
    ):
        if isinstance(field_type, str):
            field_type = FieldType.from_string(field_type)

        if item_type and isinstance(
            item_type, str
        ):  # Check item_type is not None before isinstance
            item_type = FieldType.from_string(item_type)

        self.field_type: FieldType = field_type
        self.item_type: Optional[FieldType] = item_type  # Type hint corrected
        self.is_dynamic = is_dynamic
        self.original = original
        self.enum_choices = enum_choices or []

        # Store new schema-related attributes
        self.item_schema_type = item_schema_type
        # self.item_schema = item_schema # Deferred
        self.referenced_entity_type = referenced_entity_type
        self.referenced_entity_category = referenced_entity_category

        self._raw_value = value
        self._value = self._convert_value(value)  # self._value will be set by _convert_value

    @property
    def value(self) -> Any:
        return self._value

    @value.setter
    def value(self, new_value: Any) -> None:
        self._raw_value = new_value
        self._value = self._convert_value(new_value)  # Ensure conversion on set

    def _convert_value(self, value: Any) -> Any:
        """Convert a value to the correct type."""
        if isinstance(value, hy.models.Symbol) and str(value) == "None":
            return None
        if value is None or value == "None":
            return None
        if self.field_type == FieldType.LIST and self.item_schema_type:
            if isinstance(value, (hy.models.List, list)):
                return [item if isinstance(item, hy.models.Object) else item for item in value]
            logger.warning(
                f"LIST with item_schema_type '{self.item_schema_type}' received non-list value: {type(value)}. Value: {value}"
            )
            return hy_to_python(value)  # Attempt conversion

        if isinstance(value, hy.models.Expression):
            if self.field_type == FieldType.DATETIME:
                logger.debug(
                    f"DATETIME field receives HyExpression '{value}'. Storing as HyExpression for loader evaluation."
                )
                return value  # Store the HyExpression directly
            if self.field_type == FieldType.ENTITY_REFERENCE:
                logger.debug(
                    f"ENTITY_REFERENCE field receives HyExpression '{value}'. Storing as HyExpression for loader evaluation."
                )
                return value  # Store the HyExpression directly
            if self.field_type == FieldType.CODE:
                logger.debug(
                    f"CODE field receives HyExpression '{value}'. Storing as HyExpression."
                )
                return value  # Store the HyExpression directly for CODE type

        if self.field_type == FieldType.ENTITY_REFERENCE:
            if isinstance(value, str):
                return None if value == "None" else value
            if isinstance(value, (hy.models.String, hy.models.Symbol)):
                return str(value)
            if isinstance(value, dict):
                return value
            logger.warning(
                f"ENTITY_REFERENCE field received unexpected value type {type(value)}: '{value}'. Storing as is."
            )
            return value

        if self.field_type == FieldType.DATETIME:
            if value is None or value == "None":
                return None
            if isinstance(value, datetime.datetime) or isinstance(value, DecimalTimeStamp):
                return value
            logger.warning(
                f"DATETIME field received unexpected value type {type(value)}: '{value}'. Storing as is."
            )
            return hy_to_python(value)

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
                    return py_value.lower() in ("true", "yes", "1", "t", "y")
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

                if isinstance(py_value, dict) and "start" in py_value and "duration" in py_value:
                    start = py_value["start"]
                    if not isinstance(start, DecimalTimeStamp):
                        start = DecimalTimeStamp(start)

                    duration = py_value["duration"]
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
                current_list_val = py_value
                if not isinstance(current_list_val, list):
                    if isinstance(current_list_val, str):
                        try:
                            loaded_json = json.loads(current_list_val)
                            if isinstance(loaded_json, list):
                                current_list_val = loaded_json
                            else:
                                current_list_val = [loaded_json]  # Wrap non-list JSON into a list
                        except json.JSONDecodeError:
                            current_list_val = [current_list_val]  # Treat as a single-item list
                    else:
                        current_list_val = [
                            current_list_val
                        ]  # Wrap non-list, non-string into a list

                if self.item_type and current_list_val:  # Ensure current_list_val is not empty
                    return current_list_val
                return current_list_val  # Return list of Python natives

            elif self.field_type == FieldType.DICT:
                current_dict_val = py_value
                if not isinstance(current_dict_val, dict):
                    if isinstance(current_dict_val, str):
                        try:
                            loaded_json = json.loads(current_dict_val)
                            if isinstance(loaded_json, dict):
                                current_dict_val = loaded_json
                            else:
                                current_dict_val = {"value": loaded_json}
                        except json.JSONDecodeError:
                            current_dict_val = {"value": current_dict_val}  # Wrap into a dict
                    else:
                        current_dict_val = {
                            "value": current_dict_val
                        }  # Wrap non-dict, non-string into a dict

                if self.item_type and current_dict_val:
                    return {
                        k: TypedValue(v, self.item_type).value for k, v in current_dict_val.items()
                    }
                return current_dict_val  # Return dict of Python natives

            elif self.field_type == FieldType.CODE:
                return py_value

            else:
                logger.warning(
                    f"Unknown FieldType '{self.field_type}' encountered for value '{value}'. "
                    f"Storing hy_to_python converted value: '{py_value}'."
                )
                return py_value

        except Exception as e:
            # Log the error and return None for conversion errors
            logger.error(f"Error converting value {py_value} to type {self.field_type}: {e}")
            return None

    def serialize(self) -> Dict[str, Any]:
        result = {
            "type": str(self.field_type),
            "value": self._serialize_value(),  # self._value is already converted
        }

        if self.item_type:
            result["item_type"] = str(self.item_type)
        if self.is_dynamic:
            result["is_dynamic"] = True
        if self.original:
            result["original"] = self.original
        if self.field_type == FieldType.ENUM and self.enum_choices:
            result["enum_choices"] = self.enum_choices

        # Add new schema info for API
        if self.item_schema_type:
            result["item_schema_type"] = self.item_schema_type
        if self.referenced_entity_type:
            result["referenced_entity_type"] = self.referenced_entity_type
        if self.referenced_entity_category:
            result["referenced_entity_category"] = self.referenced_entity_category

        return result

    def serialize_for_persistence(self) -> str:
        if self.is_dynamic and self.original:
            return self.original

        # For LIST of complex objects where self._value is List[HyExpression]
        if (
            self.field_type == FieldType.LIST
            and self.item_schema_type
            and isinstance(self._value, list)
        ):
            # Assuming self._value contains HyExpression objects or other Hy models
            # format_value should handle a list of Hy objects correctly.
            return format_value(self._value)  # format_value will call hy.repr on HyExpressions

        # For ENTITY_REFERENCE (static) where self._value is the key string
        if self.field_type == FieldType.ENTITY_REFERENCE and not self.is_dynamic:
            return format_value(self._value)  # Should quote the string key

        if self.field_type == FieldType.CODE:
            if isinstance(self.value, (Expression, Symbol)):
                return hy.repr(self.value)
            if isinstance(self.value, str):
                stripped_val = self.value.strip()
                if stripped_val.startswith("(") and stripped_val.endswith(")"):
                    return self.value

        return format_value(self.value)

    def _serialize_value(self) -> Any:
        """Convert the value to a serializable format."""
        val_to_serialize = self.value

        if val_to_serialize is None:
            return None

        if self.field_type == FieldType.CODE and isinstance(val_to_serialize, (Expression, Symbol)):
            return hy.repr(val_to_serialize)

        if self.field_type == FieldType.LIST and self.item_schema_type:
            if isinstance(val_to_serialize, list):
                return [
                    item.serialize() if isinstance(item, TypedValue) else item
                    for item in val_to_serialize
                ]
            return val_to_serialize  # Fallback

        if self.field_type == FieldType.DATETIME:
            if isinstance(val_to_serialize, datetime.datetime):
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

        elif self.field_type == FieldType.LIST:  # Primitives
            if isinstance(val_to_serialize, list):
                # Assuming items are already Python natives due to recursive TypedValue in _convert_value
                return val_to_serialize
            return val_to_serialize

        elif self.field_type == FieldType.DICT:  # Primitives in values
            if isinstance(val_to_serialize, dict):
                # Assuming values are already Python natives
                return val_to_serialize
            return val_to_serialize

        else:  # For STRING, INTEGER, BOOLEAN, CODE (if Python string), ENUM etc.
            return val_to_serialize

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> "TypedValue":
        """Create a TypedValue from a serialized dictionary."""
        if not isinstance(data, dict):
            logger.warning(
                f"Attempting to deserialize non-dict data: {data}. Assuming STRING type."
            )
            return cls(data, FieldType.STRING)

        field_type_str = data.get("type", FieldType.STRING.value)  # Ensure .value for comparison
        value = data.get("value")
        item_type_str = data.get("item_type")
        is_dynamic = data.get("is_dynamic", False)
        original = data.get("original")
        enum_choices = data.get("enum_choices", [])

        # New schema fields from serialized data
        item_schema_type = data.get("item_schema_type")
        referenced_entity_type = data.get("referenced_entity_type")
        referenced_entity_category = data.get("referenced_entity_category")

        field_type_enum = FieldType.from_string(field_type_str)
        item_type_enum = FieldType.from_string(item_type_str) if item_type_str else None

        if field_type_enum == FieldType.LIST and item_schema_type and isinstance(value, list):
            processed_value_list = []
            for item_str in value:
                if isinstance(item_str, str) and item_str.strip().startswith("("):
                    try:
                        # Assuming each item_str is a single, complete S-expression
                        parsed_item = next(iter(hy.read_many(item_str)), None)
                        if parsed_item is not None:
                            processed_value_list.append(parsed_item)
                        else:
                            logger.warning(
                                f"Failed to parse list item S-expression string: '{item_str}'. Appending as string."
                            )
                            processed_value_list.append(item_str)  # Fallback
                    except Exception as e:
                        logger.error(
                            f"Error hy.read_many on list item '{item_str}': {e}. Appending as string."
                        )
                        processed_value_list.append(item_str)  # Fallback
                else:
                    processed_value_list.append(item_str)  # Not an S-expression string
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
                    value = parsed_value  # Convert S-expression string to HyExpression
                else:
                    logger.warning(
                        f"Failed to parse entity_reference S-expression string: '{value}'. Using as string."
                    )
            except Exception as e:
                logger.error(
                    f"Error hy.read_many on entity_reference value '{value}': {e}. Using as string."
                )

        # The constructor's _convert_value will handle further processing based on type
        return cls(
            value=value,  # Pass potentially HyExpression objects
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

    if isinstance(value, datetime.datetime):
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
        return FieldType.LIST  # Includes HyList
    if isinstance(value, dict) or isinstance(value, hy.models.Dict):
        return FieldType.DICT  # Includes HyDict

    if isinstance(value, Expression):
        return FieldType.CODE

    if isinstance(value, str) and value.strip().startswith("(") and value.strip().endswith(")"):
        try:
            parsed_hy = hy.read(value)
            if isinstance(parsed_hy, (Expression, Symbol)):
                return FieldType.CODE
        except Exception:
            pass  # Not a valid Hy expression, treat as plain string

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
