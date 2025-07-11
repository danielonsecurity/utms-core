from io import StringIO
from typing import List, TYPE_CHECKING

import hy

from utms.core.mixins import LoggerMixin
from utms.core.plugins.registry import plugin_registry

if TYPE_CHECKING:
    from utms.utms_types import HyNode

from .utils import format_expression


class HyAST(LoggerMixin):
    """Base AST manager for Hy code."""

    def parse_file(self, filename: str) -> List["HyNode"]:
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
            self.logger.error(f"Error parsing {filename}: {e}")
            raise

        return self._parse_expressions(expressions, line_comments)

    def _parse_expressions(self, expressions: List, comments: dict) -> List["HyNode"]:
        """Convert Hy expressions into our AST nodes."""
        nodes = []
        self.logger.debug("Parsing %s expressions", len(expressions))

        for expr in expressions:
            if isinstance(expr, hy.models.Expression):
                expr_type = str(expr[0])
                self.logger.debug("Looking for plugin for expression type: %s", expr_type)
                self.logger.debug("Available plugins: %s", plugin_registry.list_node_plugins())
                plugin = plugin_registry.get_node_plugin(expr_type)
                if plugin:
                    self.logger.debug("Found plugin for %s %s", expr_type, plugin)
                    try:
                        node = plugin.parse(expr)
                        if node:
                            self.logger.debug("Successfully parsed node: %s", node)
                            nodes.append(node)

                    except Exception as e:
                        self.logger.error(f"Error parsing {expr_type} with plugin: {e}")
                        import traceback

                        self.logger.error(traceback.format_exc())
                else:
                    self.logger.warning(f"No plugin found for expression type: {expr_type}")
                    self.logger.debug("Available plugins: %s", plugin_registry.list_node_plugins())

        return nodes

    def to_hy(self, nodes: List["HyNode"]) -> str:
        """Convert AST nodes back to Hy code."""
        lines = []

        # Add header comments
        if hasattr(self, "header_comments"):
            lines.extend(self.header_comments)
            if self.header_comments:
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
                lines.extend(format_expression(str(node.original).strip("'")))
            else:
                plugin = plugin_registry.get_node_plugin(node.type)
                if plugin:
                    try:
                        formatted_lines = plugin.format(node)
                        lines.extend(formatted_lines)
                    except Exception as e:
                        self.logger.error(f"Error formatting node {node.type}: {e}")
                else:
                    self.logger.warning(f"No plugin found for node type: {node.type}")

            # Add blank line between nodes
            if i < len(nodes) - 1:
                lines.append("")

        # Remove trailing blank lines
        while lines and not lines[-1].strip():
            lines.pop()

        return "\n".join(lines)
