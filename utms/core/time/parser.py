import math
import re
from decimal import Decimal
from typing import List

import hy

from utms.core.hy.evaluation import evaluate_hy_expression
from utms.core.time import DecimalTimeLength


class TimeExpressionParser:
    """
    Parses human-readable time expressions (e.g., "2 minutes + 1d") into
    evaluatable time values. This is the final, corrected version.
    """

    def __init__(self, units_provider=None):
        self.units_provider = units_provider
        self.token_pattern = re.compile(
            r"(?P<number>[+-]?(?:\d*\.)?\d+(?:e[+-]?\d+)?)" r"\s*" r"(?P<unit>[a-zA-Z]+)?"
        )
        self.operators = {
            "+": 1,
            "-": 1,
            "*": 2,
            "/": 2,
            "%": 2,
            "//": 2,
            "^": 3,
        }

    def tokenize(self, expression: str) -> List[str]:
        """Splits expression into tokens, adding '+' between adjacent time values."""
        tokens = []
        pos = 0
        expr = expression.strip()
        while pos < len(expr):
            while pos < len(expr) and expr[pos].isspace():
                pos += 1
            if pos >= len(expr):
                break
            match = self.token_pattern.match(expr, pos)
            if match:
                tokens.append(match.group(0))
                pos = match.end()
                next_pos = pos
                while next_pos < len(expr) and expr[next_pos].isspace():
                    next_pos += 1
                if next_pos < len(expr) and self.token_pattern.match(expr, next_pos):
                    tokens.append("+")
                continue
            if expr[pos] in "+-*/%^()":
                if expr[pos : pos + 2] == "//":
                    tokens.append("//")
                    pos += 2
                else:
                    tokens.append(expr[pos])
                    pos += 1
                continue
            pos += 1
        return tokens

    def to_hy_expression(self, tokens: List[str]) -> hy.models.Expression:
        """Converts tokens to a Hy expression using the shunting-yard algorithm."""
        output_queue = []
        operator_stack = []
        for token in tokens:
            match = self.token_pattern.match(token)
            if match:
                number = match.group("number")
                unit_symbol = (match.group("unit") or "s").lower()
                output_queue.append(
                    hy.models.Expression(
                        [
                            hy.models.Symbol("*"),
                            hy.models.Float(float(number)),
                            hy.models.Symbol(unit_symbol),
                        ]
                    )
                )
                continue
            if token == "(":
                operator_stack.append(token)
            elif token == ")":
                while operator_stack and operator_stack[-1] != "(":
                    op = operator_stack.pop()
                    b = output_queue.pop()
                    a = output_queue.pop()
                    output_queue.append(hy.models.Expression([hy.models.Symbol(op), a, b]))
                if operator_stack and operator_stack[-1] == "(":
                    operator_stack.pop()
            elif token in self.operators:
                while (
                    operator_stack
                    and operator_stack[-1] != "("
                    and self.operators.get(operator_stack[-1], 0) >= self.operators.get(token, 0)
                ):
                    op = operator_stack.pop()
                    b = output_queue.pop()
                    a = output_queue.pop()
                    output_queue.append(hy.models.Expression([hy.models.Symbol(op), a, b]))
                operator_stack.append(token)
        while operator_stack:
            op = operator_stack.pop()
            if op == "(":
                raise ValueError("Mismatched parentheses")
            b = output_queue.pop()
            a = output_queue.pop()
            output_queue.append(hy.models.Expression([hy.models.Symbol(op), a, b]))
        if not output_queue:
            raise ValueError("Empty expression")
        return output_queue[0]

    def parse(self, expression: str) -> hy.models.Expression:
        """Parses a full time expression into a Hy expression."""
        tokens = self.tokenize(expression)
        return self.to_hy_expression(tokens)

    def create_evaluation_context(self) -> dict:
        """
        Creates the context for Hy evaluation. This is the definitive version
        that handles casing, plurals, and data types correctly.
        """
        if not self.units_provider:
            raise ValueError("Units provider not set in TimeExpressionParser.")

        context = {}
        for _, unit_obj in self.units_provider.items():
            time_length_val = DecimalTimeLength(unit_obj.value)

            all_names_for_unit = set()

            all_names_for_unit.add(str(unit_obj.label))

            if isinstance(unit_obj.name, list):
                all_names_for_unit.update([str(n) for n in unit_obj.name])
            elif unit_obj.name is not None:
                all_names_for_unit.add(str(unit_obj.name))
            for name in all_names_for_unit:
                lower_name = name.lower()
                context[lower_name] = time_length_val
                if not lower_name.endswith('s'):
                    context[lower_name + 's'] = time_length_val

        # Add standard math functions.
        context.update(
            {
                "math": math,
                "sqrt": math.sqrt,
                "abs": abs,
                "pi": math.pi,
                "e": math.e,
            }
        )
        return context

    def evaluate(self, expression: str) -> DecimalTimeLength:
        """Parses and evaluates a time expression, returning a final time length."""
        hy_expr = self.parse(expression)
        context = self.create_evaluation_context()
        result = evaluate_hy_expression(hy_expr, context)
        return result
