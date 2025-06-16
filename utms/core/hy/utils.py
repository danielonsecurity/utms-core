from datetime import datetime
from decimal import Decimal
from typing import Any, List, Optional

import hy


def is_dynamic_content(value: Any) -> bool:
    """Determine if content is dynamic based on its structure."""
    if isinstance(value, hy.models.Symbol) and str(value) == "None":
        return False
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

def python_to_hy_string(value: Any) -> str:
    """Converts a PURE PYTHON value to a Hy string representation."""
    if isinstance(value, datetime):
        return f"(datetime {value.year} {value.month} {value.day} {value.hour} {value.minute} {value.second} {value.microsecond})"
    if isinstance(value, list):
        items = " ".join([python_to_hy_string(item) for item in value])
        return f"[{items}]"
    if isinstance(value, dict):
        pairs = []
        for k, v in value.items():
            key_str = hy.repr(hy.models.Keyword(str(k)))
            val_str = python_to_hy_string(v)
            pairs.append(f"{key_str} {val_str}")
        return f"{{{' '.join(pairs)}}}"
    return hy.repr(value)

def hy_obj_to_string(obj: hy.models.Object) -> str:
    """Correctly serializes a Hy AST object into a Hy source string."""
    if isinstance(obj, hy.models.String):
        return f'"{str(obj)}"'
    if isinstance(obj, hy.models.Symbol):
        return str(obj)
    if isinstance(obj, hy.models.Keyword):
        return str(obj)
    if isinstance(obj, hy.models.Integer):
        return str(int(obj))
    if isinstance(obj, hy.models.Float):
        return str(float(obj))

    if isinstance(obj, hy.models.List):
        items = " ".join([hy_obj_to_string(item) for item in obj])
        return f"[{items}]"

    if isinstance(obj, hy.models.Dict):
        pairs = []
        for i in range(0, len(obj), 2):
            key_str = hy_obj_to_string(obj[i])
            val_str = hy_obj_to_string(obj[i+1])
            pairs.append(f"{key_str} {val_str}")
        return f"{{{' '.join(pairs)}}}"

    if isinstance(obj, hy.models.Expression):
        items = " ".join([hy_obj_to_string(item) for item in obj])
        return f"({items})"
    raise TypeError(f"hy_obj_to_string: Unhandled hy.models type: {type(obj)}")



def get_from_hy_dict(hy_dict: hy.models.Dict, key_to_find: str, default: Any = None) -> Optional[Any]:
    """
    Safely gets a value from a hy.models.Dict by its keyword key.
    Returns the HyObject value, or the provided default if not found.
    """
    if not isinstance(hy_dict, hy.models.Dict):
        return default
        
    for i in range(0, len(hy_dict), 2):
        key = hy_dict[i]
        if isinstance(key, hy.models.Keyword) and str(key)[1:] == key_to_find:
            return hy_dict[i+1]
            
    return default


def _format_map(content: str, base_indent: int) -> str:
    """Format map content with proper indentation."""
    items = content.split()
    if len(items) <= 4:  # Short maps on one line
        return f"{{{' '.join(items)}}}"

    lines = ["{"]
    i = 0
    while i < len(items):
        if items[i].startswith(":"):
            # Key-value pair
            if i + 1 < len(items):
                lines.append(f"  {' '.join(items[i:i+2])}")
                i += 2
            else:
                lines.append(f"  {items[i]}")
                i += 1
        else:
            lines.append(f"  {items[i]}")
            i += 1
    lines.append("}")
    return "\n".join("  " * base_indent + line for line in lines)


def _format_list(content: str, base_indent: int) -> str:
    """Format list content with proper indentation."""
    items = content.split()
    if len(items) <= 4:  # Short lists on one line
        return f"[{' '.join(items)}]"

    lines = ["["]
    current_line = "  "
    for item in items:
        if len(current_line) + len(item) > 80:  # Line length limit
            lines.append(current_line.rstrip())
            current_line = "  "
        current_line += item + " "
    if current_line.strip():
        lines.append(current_line.rstrip())
    lines.append("]")
    return "\n".join("  " * base_indent + line for line in lines)


def format_expression(expr_str: str) -> List[str]:
    """Format a Hy expression with proper indentation."""

    formatted = []
    current_line = ""
    indent_level = 0
    in_string = False
    string_char = None
    i = 0

    while i < len(expr_str):
        char = expr_str[i]

        # Handle strings
        if char in "\"'":
            if not in_string:
                in_string = True
                string_char = char
            elif char == string_char and expr_str[i - 1] != "\\":
                in_string = False
                string_char = None
            current_line += char
            i += 1
            continue

        if in_string:
            current_line += char
            i += 1
            continue

        # Handle special cases
        if char == "{":
            # Find matching closing brace
            brace_count = 1
            j = i + 1
            while j < len(expr_str) and brace_count > 0:
                if expr_str[j] == "{":
                    brace_count += 1
                elif expr_str[j] == "}":
                    brace_count -= 1
                j += 1
            map_content = expr_str[i + 1 : j - 1].strip()
            current_line += _format_map(map_content, indent_level)
            i = j
            continue

        if char == "[":
            # Find matching closing bracket
            bracket_count = 1
            j = i + 1
            while j < len(expr_str) and bracket_count > 0:
                if expr_str[j] == "[":
                    bracket_count += 1
                elif expr_str[j] == "]":
                    bracket_count -= 1
                j += 1
            list_content = expr_str[i + 1 : j - 1].strip()
            current_line += _format_list(list_content, indent_level)
            i = j
            continue

        if char == "(":
            if current_line.strip():
                formatted.append(current_line)
                current_line = "  " * indent_level + "("
            else:
                current_line += "("
            indent_level += 1
            i += 1
            continue

        if char == ")":
            indent_level -= 1
            current_line += ")"
            if indent_level == 0:
                formatted.append(current_line)
                current_line = ""
            i += 1
            continue

        current_line += char
        i += 1

    if current_line:
        formatted.append(current_line)

    return formatted
