
from typing import Any
import hy


def hy_to_python(data: Any) -> Any:
    """Convert Hy model objects to Python values.

    Args:
        value: Any value, potentially a Hy model object
        
    Returns:
        Equivalent Python value
    """
    if data is None:
        return None
        
    if isinstance(data, (hy.models.String, hy.models.Symbol)):
        return str(data)
        
    if isinstance(data, hy.models.Integer):
        return int(data)
        
    if isinstance(data, hy.models.Float):
        return float(data)
        
    if isinstance(data, hy.models.Keyword):
        # Convert :keyword to "keyword"
        return str(data)[1:]
        
    if isinstance(data, (hy.models.List, hy.models.Expression, list, tuple)):
        return [hy_to_python(item) for item in data]
        
    if isinstance(data, (hy.models.Dict, dict)):
        return {hy_to_python(k): hy_to_python(v) for k, v in data.items()}

    return data



    # if isinstance(value, hy.models.String):
    #     return str(value)
    # elif isinstance(value, hy.models.Integer):
    #     return int(value)
    # elif isinstance(value, hy.models.Float):
    #     return float(value)
    # elif isinstance(value, hy.models.List):
    #     return [hy_to_python(item) for item in value]
    # elif isinstance(value, list):
    #     return [hy_to_python(item) for item in value]
    # elif isinstance(value, hy.models.Dict):
    #     # Handle Hy dicts which are stored as [k1, v1, k2, v2, ...]
    #     result = {}
    #     for k, v in zip(value[::2], value[1::2]):
    #         key = str(k).replace(':', '')  # Remove ':' from keywords
    #         result[key] = hy_to_python(v)
    #     return result
    # return value


def format_hy_value(v: Any) -> str:
    """Format a value for Hy syntax."""
    if isinstance(v, hy.models.String):
        return f'"{str(v)}"'
    elif isinstance(v, hy.models.Integer):
        return str(int(v))  # Just get the integer value
    elif isinstance(v, hy.models.Float):
        return str(float(v))  # Just get the float value
    elif isinstance(v, hy.models.List):
        items = " ".join(format_hy_value(item) for item in v)
        return f"[{items}]"
    elif isinstance(v, str):
        return f'"{v}"'
    elif isinstance(v, list):
        items = " ".join(format_hy_value(item) for item in v)
        return f"[{items}]"
    else:
        return str(v)
