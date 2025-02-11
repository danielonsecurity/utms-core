from dataclasses import dataclass
from datetime import datetime
from io import StringIO
from typing import Any, List, Optional
from decimal import Decimal

import hy

from utms.core.formats import TimeUncertainty
from utms.utils import get_logger
from utms.utms_types import is_dict, is_list, is_string

logger = get_logger("resolvers.hy_ast")


@dataclass
class HyNode:
    """A node in the Hy AST."""

    type: str  # 'def-anchor', 'def-event', 'property', 'value', 'comment'
    value: Any  # The actual value/content
    children: Optional[List["HyNode"]] = None
    comment: Optional[str] = None  # Associated comment if any
    original: Any = None  # Original Hy expression
    is_dynamic: bool = False

    def __post_init__(self):
        self.children = self.children or []


class HyAST:
    """Simple AST manager for Hy code."""

    def parse_file(self, filename: str) -> List[HyNode]:
        """Parse a Hy file into our AST."""
        with open(filename) as f:
            content = f.read()

        lines = content.split("\n")

        # Store header comments (comments before first definition)
        self.header_comments = []
        line_comments = {}

        in_header = True
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith(";;"):
                if in_header:
                    self.header_comments.append(line)
                else:
                    line_comments[i] = line
            elif stripped:  # Non-empty, non-comment line
                in_header = False

        # Parse Hy code
        stream = StringIO(content)
        expressions = []

        try:
            while True:
                try:
                    expr = hy.read(stream, filename)
                    expressions.append(expr)
                except EOFError:
                    break
        except Exception as e:
            logger.error(f"Error parsing {filename}: {e}")
            raise

        return self._parse_expressions(expressions, line_comments)

    def _parse_expressions(self, expressions: List, comments: dict) -> List[HyNode]:
        """Convert Hy expressions into our AST nodes."""
        nodes = []

        for expr in expressions:
            # Store the original expression
            original = hy.repr(expr)

            if isinstance(expr, hy.models.Expression):
                if str(expr[0]) == "def-anchor":
                    nodes.append(self._parse_anchor_def(expr, original))
                elif str(expr[0]) == "def-fixed-unit":
                    nodes.append(self._parse_unit_def(expr, original))
            # Add other def types as needed
                # Add other def types as needed

        return nodes

    def _parse_unit_def(self, expr: hy.models.Expression, original: str) -> HyNode:
        """Parse a def-fixed-unit expression."""
        if len(expr) < 2:
            return None

        label = str(expr[1])  # The unit label
        properties = []

        # Process each property expression (starting from index 2)
        for prop in expr[2:]:
            if isinstance(prop, hy.models.Expression):
                prop_name = str(prop[0])
                prop_value = prop[1]

                # For dynamic expressions (like function calls or complex expressions)
                is_dynamic = self._is_dynamic_content(prop_value)

                logger.debug(f"Property: {prop_name}")
                logger.debug(f"Value: {prop_value}")
                logger.debug(f"Is dynamic: {is_dynamic}")
                logger.debug(f"Original: {hy.repr(prop_value) if is_dynamic else None}")

                # Store property with its original expression if it's dynamic
                properties.append(
                    HyNode(
                        type="property",
                        value=prop_name,
                        children=[
                            HyNode(
                                type="value",
                                value=prop_value,
                                original=hy.repr(prop_value) if is_dynamic else None,
                                is_dynamic=is_dynamic,
                            )
                        ],
                    )
                )

        return HyNode(
            type="def-fixed-unit",
            value=label,
            children=properties,
            original=original,  # Store complete original expression
        )


    def _parse_anchor_def(self, expr: hy.models.Expression, original: str) -> HyNode:
        """Parse a def-anchor expression.

        Args:
            expr: The Hy expression (hy.models.Expression)
            original: The original string representation
        """
        if len(expr) < 2:
            return None

        name = str(expr[1])  # The anchor name/label
        properties = []

        # Process each property expression (starting from index 2)
        for prop in expr[2:]:
            if isinstance(prop, hy.models.Expression):
                prop_name = str(prop[0])
                prop_value = prop[1]

                # For dynamic expressions (like function calls or complex expressions)
                is_dynamic = self._is_dynamic_content(prop_value)

                logger.debug(f"Property: {prop_name}")
                logger.debug(f"Value: {prop_value}")
                logger.debug(f"Is dynamic: {is_dynamic}")
                logger.debug(f"Original: {hy.repr(prop_value) if is_dynamic else None}")

                # Store property with its original expression if it's dynamic
                properties.append(
                    HyNode(
                        type="property",
                        value=prop_name,
                        children=[
                            HyNode(
                                type="value",
                                value=prop_value,
                                original=hy.repr(prop_value) if is_dynamic else None,
                                is_dynamic=is_dynamic,
                            )
                        ],
                    )
                )

        return HyNode(
            type="def-anchor",
            value=name,
            children=properties,
            original=original,  # Store complete original expression
        )

    def _is_dynamic_content(self, value: Any) -> bool:
        """Determine if content is dynamic based on its structure."""
        if isinstance(value, hy.models.Expression):
            return True  # Any Hy expression is considered dynamic
        if isinstance(value, hy.models.Symbol):
            # Symbols that aren't keywords are dynamic
            return not str(value).startswith(":")
        if isinstance(value, hy.models.List):
            # Check if any element in the list is dynamic
            return any(self._is_dynamic_content(x) for x in value)
        if isinstance(value, hy.models.Dict):
            # Check both keys and values in the dict
            return any(self._is_dynamic_content(x) for x in value)
        return False

    def to_hy(self, nodes: List[HyNode]) -> str:
        """Convert AST back to Hy code."""
        lines = []

        # Add header comments if any
        if hasattr(self, "header_comments"):
            for comment in self.header_comments:
                lines.append(comment)
            lines.append("")  # Empty line after header comments

        for node in nodes:
            # Add any comments associated with this node
            if node.comment:
                # Ensure comment starts with ;; and has proper indentation
                comment = node.comment.lstrip()
                if not comment.startswith(";;"):
                    comment = ";;" + comment[1:] if comment.startswith(";") else ";;" + comment
                lines.append(comment)

            if hasattr(node, "original") and node.original:
                # Remove quotes and format the expression
                expr_str = str(node.original).strip("'")
                formatted_lines = self._format_expression(expr_str)
                lines.extend(formatted_lines)
            else:
                if node.type == "def-anchor":
                    lines.extend(self._anchor_to_hy(node))
                elif node.type == "def-fixed-unit":
                    lines.extend(self._fixed_unit_to_hy(node))

            lines.append("")

        while lines and not lines[-1].strip():
            lines.pop()

        return "\n".join(lines)

    def _fixed_unit_to_hy(self, node: HyNode) -> List[str]:
        """Convert a unit node to Hy code lines."""
        lines = []
        indent = "  "

        # Start the unit definition
        lines.append(f"(def-fixed-unit {node.value}")

        # Add properties
        for prop in node.children:
            if prop.type == "property":
                value_node = prop.children[0] if prop.children else None
                if value_node:
                    if value_node.is_dynamic and value_node.original:
                        value = value_node.original
                    else:
                        value = self._format_value(value_node.value)
                    lines.append(f"{indent}({prop.value} {value})")

        # Close the definition
        lines[-1] = lines[-1] + ")"

        return lines


    def _anchor_to_hy(self, node: HyNode) -> List[str]:
        """Convert an anchor node to Hy code."""
        lines = [f"(def-anchor {node.value}"]

        for prop in node.children:
            if prop.type == "property":
                value_node = prop.children[0]
                # print(value_node)
                # breakpoint()
                if value_node.is_dynamic and value_node.original:
                    value_str = value_node.original
                else:
                    value_str = self._format_value(value_node.value)

                lines.append(f"  ({prop.value} {value_str})")

        lines.append(")")
        return lines

    def _format_value(self, value: Any) -> str:
        """Format a value as Hy code."""
        if isinstance(value, HyNode):
            if value.is_dynamic and value.original:
                return value.original
        elif isinstance(value, (hy.models.Integer, int)):  # Handle both Hy and Python integers
            return int(value)
        elif isinstance(value, (hy.models.Float, float)):  # Handle both Hy and Python floats
            return float(value)
        elif isinstance(value, (Decimal)):  # Handle Decimal and other numeric types
            return str(value)
        elif isinstance(value, bool):  # Handle booleans explicitly
            return str(value).lower()
        elif isinstance(value, hy.models.List):
            items = [self._format_value(item) for item in value]
            return f"[{' '.join(items)}]"
        elif isinstance(value, hy.models.Dict):
            # Convert dict to pairs of items
            pairs = []
            it = iter(value)
            try:
                while True:
                    k = next(it)
                    v = next(it)
                    if isinstance(k, hy.models.Keyword):
                        pairs.append(f"{k} {self._format_value(v)}")
                    else:
                        pairs.append(f"{self._format_value(k)} {self._format_value(v)}")
            except StopIteration:
                pass
            return f"{{{' '.join(pairs)}}}"
        elif isinstance(value, hy.models.Keyword):
            return str(value)
        elif isinstance(value, datetime):
            return str(value)
        elif isinstance(value, list):
            items = [self._format_value(item) for item in value]
            return f"[{' '.join(items)}]"
        elif isinstance(value, dict):
            pairs = [f":{k} {self._format_value(v)}" for k, v in value.items()]
            return f"{{{' '.join(pairs)}}}"
        elif isinstance(value, TimeUncertainty):
            return f"{{:absolute {value.absolute:.0e} :relative {value.relative:.0e}}}"
        if isinstance(value, hy.models.String):
            return f'"{value}"'
        if isinstance(value, str):
            return f'"{value}"'
        return str(value)

    # def _format_value(self, value: Any) -> str:
    #     """Format a value as Hy code."""
    #     if isinstance(value, HyNode):
    #         if value.is_dynamic and value.original:
    #             return value.original
    #     if isinstance(value, hy.models.String):
    #         return f'"{value}"'
    #     if isinstance(value, str):
    #         return f'"{value}"'
    #     elif isinstance(value, hy.models.Integer):
    #         return str(int(value))
    #     elif isinstance(value, hy.models.Float):
    #         return str(float(value))
    #     elif isinstance(value, hy.models.List):
    #         items = [self._format_value(item) for item in value]
    #         return f"[{' '.join(items)}]"
    #     elif isinstance(value, hy.models.Dict):
    #         # Convert dict to pairs of items
    #         pairs = []
    #         it = iter(value)
    #         try:
    #             while True:
    #                 k = next(it)
    #                 v = next(it)
    #                 if isinstance(k, hy.models.Keyword):
    #                     pairs.append(f"{k} {self._format_value(v)}")
    #                 else:
    #                     pairs.append(f"{self._format_value(k)} {self._format_value(v)}")
    #         except StopIteration:
    #             pass
    #         return f"{{{' '.join(pairs)}}}"
    #     elif isinstance(value, hy.models.Keyword):
    #         return str(value)
    #     elif isinstance(value, datetime):
    #         return str(value)
    #     elif isinstance(value, list):
    #         items = [self._format_value(item) for item in value]
    #         return f"[{' '.join(items)}]"
    #     elif isinstance(value, dict):
    #         pairs = [f":{k} {self._format_value(v)}" for k, v in value.items()]
    #         return f"{{{' '.join(pairs)}}}"
    #     elif isinstance(value, TimeUncertainty):
    #         return f"{{:absolute {value.absolute:.0e} :relative {value.relative:.0e}}}"
    #     return str(value)

    def _format_expression(self, expr_str: str) -> List[str]:
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
