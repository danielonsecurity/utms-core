from io import StringIO
from typing import Any, List

import hy

from utms.utils import get_logger
from .formatters import (
    format_anchor_to_hy,
    format_expression,
    format_pattern_to_hy,
    format_unit_to_hy,
    format_variable_to_hy,
)
from .node import HyNode
from .parsers import parse_anchor_def, parse_pattern_def, parse_unit_def, parse_variable_def

logger = get_logger("resolvers.ast.base")


class HyAST:
    """Base AST manager for Hy code."""

    def parse_file(self, filename: str) -> List[HyNode]:
        """Parse a Hy file into our AST."""
        with open(filename) as f:
            content = f.read()

        lines = content.split("\n")

        # Store header comments
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
                    nodes.append(parse_anchor_def(expr, original))
                elif str(expr[0]) == "def-fixed-unit":
                    nodes.append(parse_unit_def(expr, original))
                elif str(expr[0]) == "def-var":
                    nodes.append(parse_variable_def(expr, original))
                elif str(expr[0]) == "def-pattern":
                    nodes.append(parse_pattern_def(expr, original))

        return nodes

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
        lines = []

        # Add header comments
        if hasattr(self, "header_comments"):
            for comment in self.header_comments:
                lines.append(comment)
            lines.append("")

        # Process each node
        for i, node in enumerate(nodes):
            # Add node's comment if present
            if node.comment:
                comment = node.comment.lstrip()
                if not comment.startswith(";;"):
                    comment = ";;" + comment[1:] if comment.startswith(";") else ";;" + comment
                lines.append(comment)

            # Format the node
            if hasattr(node, "original") and node.original:
                expr_str = str(node.original).strip("'")
                formatted_lines = format_expression(expr_str)
                lines.extend(formatted_lines)
            else:
                if node.type == "def-pattern":
                    lines.extend(format_pattern_to_hy(node))
                elif node.type == "def-anchor":
                    lines.extend(format_anchor_to_hy(node))
                elif node.type == "def-fixed-unit":
                    lines.extend(format_unit_to_hy(node))
                elif node.type == "def-var":
                    lines.extend(format_variable_to_hy(node))

            # Add blank line between patterns
            if i < len(nodes) - 1:
                lines.append("")

        # Remove trailing blank lines
        while lines and not lines[-1].strip():
            lines.pop()

        return "\n".join(lines)
