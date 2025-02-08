from dataclasses import dataclass
from typing import Any, List, Optional
from io import StringIO
from utms.utils import get_logger
import hy

logger = get_logger("resolvers.hy_ast")


@dataclass
class HyNode:
    """A node in the Hy AST."""
    type: str          # 'def-anchor', 'def-event', 'property', 'value', 'comment'
    value: Any         # The actual value/content
    children: Optional[List['HyNode']] = None
    comment: Optional[str] = None  # Associated comment if any
    original: Any = None  # Original Hy expression

    def __post_init__(self):
        self.children = self.children or []

class HyAST:
    """Simple AST manager for Hy code."""
    
    def parse_file(self, filename: str) -> List[HyNode]:
        """Parse a Hy file into our AST."""
        with open(filename) as f:
            content = f.read()

        lines = content.split('\n')

        # Store header comments (comments before first definition)
        self.header_comments = []
        line_comments = {}

        in_header = True
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith(';;'):
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
                if str(expr[0]) == 'def-anchor':
                    nodes.append(self._parse_anchor_def(expr, original))
                # Add other def types as needed
            
        return nodes
    
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
                is_dynamic = (
                    isinstance(prop_value, hy.models.Expression) or
                    isinstance(prop_value, hy.models.Symbol) or
                    (isinstance(prop_value, hy.models.List) and 
                     any(isinstance(x, (hy.models.Expression, hy.models.Symbol)) 
                         for x in prop_value))
                )

                # Store property with its original expression if it's dynamic
                properties.append(HyNode(
                    type='property',
                    value=prop_name,
                    children=[HyNode(
                        type='value',
                        value=prop_value,
                        original=hy.repr(prop_value) if is_dynamic else None
                    )]
                ))

        return HyNode(
            type='def-anchor',
            value=name,
            children=properties,
            original=original  # Store complete original expression
        )

    def to_hy(self, nodes: List[HyNode]) -> str:
        """Convert AST back to Hy code."""
        lines = []

        # Add header comments if any
        if hasattr(self, 'header_comments'):
            for comment in self.header_comments:
                lines.append(comment)
            lines.append("")  # Empty line after header comments

        for node in nodes:
            # Add any comments associated with this node
            if node.comment:
                # Ensure comment starts with ;; and has proper indentation
                comment = node.comment.lstrip()
                if not comment.startswith(';;'):
                    comment = ';;' + comment[1:] if comment.startswith(';') else ';;' + comment
                lines.append(comment)

            if hasattr(node, 'original') and node.original:
                # Remove quotes and format the expression
                expr_str = str(node.original).strip("'")
                formatted_lines = self._format_expression(expr_str)
                lines.extend(formatted_lines)
            else:
                if node.type == 'def-anchor':
                    lines.extend(self._anchor_to_hy(node))

            lines.append("")

        while lines and not lines[-1].strip():
            lines.pop()

        return '\n'.join(lines)


    def _anchor_to_hy(self, node: HyNode) -> List[str]:
        """Convert an anchor node to Hy code."""
        lines = [f"(def-anchor {node.value}"]
        
        for prop in node.children:
            if prop.type == 'property':
                value_node = prop.children[0]
                if hasattr(value_node, 'original') and value_node.original:
                    # Use original expression for dynamic values
                    value_str = str(value_node.original)
                else:
                    # Format static values
                    value_str = self._format_value(value_node.value)
                    
                lines.append(f"  ({prop.value} {value_str})")
        
        lines.append(")")
        return lines
    
    def _format_value(self, value: Any) -> str:
        """Format a Python value as Hy code."""
        if isinstance(value, str):
            return f'"{value}"'
        elif isinstance(value, list):
            items = " ".join(self._format_value(v) for v in value)
            return f"[{items}]"
        elif isinstance(value, dict):
            items = []
            for k, v in value.items():
                key = f":{k}" if not k.startswith(':') else k
                items.append(f"  {key} {self._format_value(v)}")
            return "{\n" + "\n".join(items) + "\n}"
        return str(value)

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
                if items[i].startswith(':'):
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
            return '\n'.join("  " * base_indent + line for line in lines)

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
            return '\n'.join("  " * base_indent + line for line in lines)

        formatted = []
        current_line = ""
        indent_level = 0
        in_string = False
        string_char = None
        i = 0

        while i < len(expr_str):
            char = expr_str[i]

            # Handle strings
            if char in '"\'':
                if not in_string:
                    in_string = True
                    string_char = char
                elif char == string_char and expr_str[i-1] != '\\':
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
            if char == '{':
                # Find matching closing brace
                brace_count = 1
                j = i + 1
                while j < len(expr_str) and brace_count > 0:
                    if expr_str[j] == '{': brace_count += 1
                    elif expr_str[j] == '}': brace_count -= 1
                    j += 1
                map_content = expr_str[i+1:j-1].strip()
                current_line += format_map(map_content, indent_level)
                i = j
                continue

            if char == '[':
                # Find matching closing bracket
                bracket_count = 1
                j = i + 1
                while j < len(expr_str) and bracket_count > 0:
                    if expr_str[j] == '[': bracket_count += 1
                    elif expr_str[j] == ']': bracket_count -= 1
                    j += 1
                list_content = expr_str[i+1:j-1].strip()
                current_line += format_list(list_content, indent_level)
                i = j
                continue

            if char == '(':
                if current_line.strip():
                    formatted.append(current_line)
                    current_line = "  " * indent_level + "("
                else:
                    current_line += "("
                indent_level += 1
                i += 1
                continue

            if char == ')':
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
