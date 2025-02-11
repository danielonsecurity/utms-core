from typing import Any, Dict, List, Optional, Tuple, TypeAlias, TypeGuard, Union

from ..base.types import FilePath

ConfigKey: TypeAlias = Union[str, int]
ParsedKey: TypeAlias = List[ConfigKey]

JsonPrimitive: TypeAlias = Union[str, int, float, bool, None]
JsonValue: TypeAlias = Union[JsonPrimitive, List["JsonValue"], Dict[str, "JsonValue"]]
JsonArray: TypeAlias = List["JsonValue"]
JsonObject: TypeAlias = Dict[str, "JsonValue"]

ConfigValue: TypeAlias = Union[JsonValue, str]
ConfigData: TypeAlias = Union[JsonArray, JsonObject]

TraverseResult: TypeAlias = Tuple[ConfigData, ConfigKey]

NestedConfig: TypeAlias = JsonObject
ConfigIndex: TypeAlias = int
ConfigPath: TypeAlias = FilePath


def is_json_primitive(value: Any) -> TypeGuard[JsonPrimitive]:
    """Check if a value is a JSON primitive type."""
    return value is None or isinstance(value, (str, int, float, bool))


def is_json_value(value: Any) -> TypeGuard[JsonValue]:
    """Check if a value is a valid JSON value."""
    if is_json_primitive(value):
        return True
    if isinstance(value, list):
        return all(is_json_value(item) for item in value)
    if isinstance(value, dict):
        return all(isinstance(k, str) and is_json_value(v) for k, v in value.items())
    return False


def is_config_value(value: Any) -> TypeGuard[ConfigValue]:
    """Check if a value is a valid config value."""
    return isinstance(value, str) or is_json_value(value)
