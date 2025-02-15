from typing import Any
import hy

def is_dynamic_content(value: Any) -> bool:
    """Determine if content is dynamic based on its structure."""
    if isinstance(value, hy.models.Expression):
        return True  # Any Hy expression is considered dynamic
    if isinstance(value, hy.models.Symbol):
        # Symbols that aren't keywords are dynamic
        return not str(value).startswith(":")
    if isinstance(value, hy.models.List):
        # Check if any element in the list is dynamic
        return any(is_dynamic_content(x) for x in value)
    if isinstance(value, hy.models.Dict):
        # Check both keys and values in the dict
        return any(is_dynamic_content(x) for x in value)
    return False
