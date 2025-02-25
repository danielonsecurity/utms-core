from datetime import datetime
from decimal import Decimal
from typing import Any, List

import hy

from utms.core.formats import TimeUncertainty
from utms.utils import get_logger

from ..node import HyNode

logger = get_logger("resolvers.ast.formatters.common")


def format_value(value: Any) -> str:
    """Format a value as Hy code."""
    if isinstance(value, HyNode):
        if value.is_dynamic and value.original:
            return value.original
    elif isinstance(value, (hy.models.Integer, int)):
        return str(int(value))
    elif isinstance(value, (hy.models.Float, float)):
        return str(float(value))
    elif isinstance(value, Decimal):
        return str(value)
    elif isinstance(value, bool):
        return str(value).lower()
    elif isinstance(value, hy.models.List):
        items = [format_value(item) for item in value]
        return f"[{' '.join(items)}]"
    elif isinstance(value, hy.models.Dict):
        pairs = []
        it = iter(value)
        try:
            while True:
                k = next(it)
                v = next(it)
                if isinstance(k, hy.models.Keyword):
                    pairs.append(f"{k} {format_value(v)}")
                else:
                    pairs.append(f"{format_value(k)} {format_value(v)}")
        except StopIteration:
            pass
        return f"{{{' '.join(pairs)}}}"
    elif isinstance(value, hy.models.Keyword):
        return str(value)
    elif isinstance(value, datetime):
        return str(value)
    elif isinstance(value, list):
        items = [format_value(item) for item in value]
        return f"[{' '.join(items)}]"
    elif isinstance(value, dict):
        pairs = [f":{k} {format_value(v)}" for k, v in value.items()]
        return f"{{{' '.join(pairs)}}}"
    elif isinstance(value, TimeUncertainty):
        return f"{{:absolute {value.absolute:.0e} :relative {value.relative:.0e}}}"
    elif isinstance(value, (hy.models.String, str)):
        return f'"{value}"'
    return str(value)


def format_expression(expr_str: str) -> List[str]:
    """Format a Hy expression with proper indentation."""

    def format_map(content: str, base_indent: int) -> str:
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

    def format_list(content: str, base_indent: int) -> str:
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
            current_line += format_map(map_content, indent_level)
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
            current_line += format_list(list_content, indent_level)
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
