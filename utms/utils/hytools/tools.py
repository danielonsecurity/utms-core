
from typing import Any
from decimal import Decimal
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

def list_to_dict(flat_list):
    return dict(zip(flat_list[::2], flat_list[1::2]))

def python_to_hy(value: Any) -> str:
    """Format a Python value as a Hy expression."""
    if value is None:
        return "None"
    elif isinstance(value, bool):
        return "true" if value else "false"
    elif isinstance(value, (int, Decimal)):
        return str(value)
    elif isinstance(value, str):
        return f'"{value}"'
    elif isinstance(value, list):
        items = " ".join(python_to_hy(item) for item in value)
        return f"[{items}]"
    elif isinstance(value, dict):
        if not value:
            return "{}"
        items = []
        for k, v in value.items():
            # Format key as a keyword
            key = f":{k}" if not k.startswith(':') else k
            items.append(f"  {key} {python_to_hy(v)}")
        return "{\n" + "\n".join(items) + "\n}"
    return str(value)
