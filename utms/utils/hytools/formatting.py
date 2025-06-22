from typing import Any

import hy


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
