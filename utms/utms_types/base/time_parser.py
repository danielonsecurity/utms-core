# import re
# import math
# from typing import List, Tuple
# from decimal import Decimal
# import hy
# from utms.core.time import DecimalTimeLength
# from utms.resolvers import evaluate_hy_expression
# from utms.core.config import Config

# config = Config()

# class TimeExpressionParser:
#     """Converts human-readable time expressions to Hy expressions"""

#     def __init__(self):
#         self.token_pattern = re.compile(
#             r'(?P<number>[+-]?(?:\d*\.)?\d+(?:e[+-]?\d+)?)'
#             r'\s*'
#             r'(?P<unit>[a-zA-Z]+)?'
#         )
#         self.operators = {
#             '+': 1,    # Addition
#             '-': 1,    # Subtraction
#             '*': 2,    # Multiplication
#             '/': 2,    # Division
#             '%': 2,    # Modulo
#             '//': 2,   # Floor division
#             '^': 3,    # Power (highest precedence)
#         }

#     def tokenize(self, expression: str) -> List[str]:
#         """Split expression into tokens, adding '+' between time values"""
#         tokens = []
#         pos = 0
#         expr = expression.strip()

#         while pos < len(expr):
#             # Skip whitespace
#             while pos < len(expr) and expr[pos].isspace():
#                 pos += 1
#             if pos >= len(expr):
#                 break

#             # Try to match number+unit
#             match = self.token_pattern.match(expr, pos)
#             if match:
#                 tokens.append(match.group(0))
#                 pos = match.end()

#                 # Look ahead for another number+unit after whitespace
#                 next_pos = pos
#                 while next_pos < len(expr) and expr[next_pos].isspace():
#                     next_pos += 1
#                 if next_pos < len(expr):
#                     next_match = self.token_pattern.match(expr, next_pos)
#                     if next_match:
#                         tokens.append('+')  # Insert '+' between time values
#                 continue

#             # Check for operators and parentheses
#             if expr[pos] in '+-*/%^()':
#                 if expr[pos:pos+2] == '//':
#                     tokens.append('//')
#                     pos += 2
#                 else:
#                     tokens.append(expr[pos])
#                     pos += 1
#                 continue

#             pos += 1

#         return tokens

#     def parse_time_value(self, value: str, unit: str = None) -> hy.models.Expression:
#         """Convert a number and unit into a Hy expression"""
#         if unit is None:
#             # Default to seconds if no unit specified
#             unit = 's'
#         return hy.models.Expression([
#                  hy.models.Symbol("*"),
#                  hy.models.Float(float(value)),
#                  hy.models.Symbol(unit)
#                  ])


#     def to_hy_expression(self, tokens: List[str]) -> hy.models.Expression:
#         """Convert tokens to Hy expression using shunting yard algorithm"""
#         output_queue = []  # for postfix expression
#         operator_stack = []

#         for token in tokens:
#             # Handle numbers with units
#             match = self.token_pattern.match(token)
#             if match:
#                 number = match.group('number')
#                 unit = match.group('unit') or 's'
#                 output_queue.append(hy.models.Expression([
#                     hy.models.Symbol('*'),
#                     hy.models.Float(float(number)),
#                     hy.models.Symbol(unit)
#                 ]))
#                 continue

#             if token == '(':
#                 operator_stack.append(token)
#             elif token == ')':
#                 # Process operators until we find the matching '('
#                 while operator_stack and operator_stack[-1] != '(':
#                     op = operator_stack.pop()
#                     b = output_queue.pop()
#                     a = output_queue.pop()
#                     output_queue.append(hy.models.Expression([
#                         hy.models.Symbol(op),
#                         a,
#                         b
#                     ]))
#                 # Remove the '('
#                 if operator_stack and operator_stack[-1] == '(':
#                     operator_stack.pop()
#             elif token in self.operators:
#                 # Process operators with higher or equal precedence
#                 while (operator_stack and operator_stack[-1] != '(' and
#                        self.operators.get(operator_stack[-1], 0) >= self.operators.get(token, 0)):
#                     op = operator_stack.pop()
#                     b = output_queue.pop()
#                     a = output_queue.pop()
#                     output_queue.append(hy.models.Expression([
#                         hy.models.Symbol(op),
#                         a,
#                         b
#                     ]))
#                 operator_stack.append(token)

#         # Process remaining operators
#         while operator_stack:
#             op = operator_stack.pop()
#             if op == '(':
#                 raise ValueError("Mismatched parentheses")
#             b = output_queue.pop()
#             a = output_queue.pop()
#             output_queue.append(hy.models.Expression([
#                 hy.models.Symbol(op),
#                 a,
#                 b
#             ]))

#         if not output_queue:
#             raise ValueError("Empty expression")

#         return output_queue[0]


#     def restructure_expression(self, expr: hy.models.Expression) -> hy.models.Expression:
#         """Convert postfix expression to prefix (Hy) expression"""
#         # If there's only one element, return it directly
#         if len(expr) == 1:
#             return expr[0]

#         stack = []
#         for token in expr:
#             if isinstance(token, hy.models.Symbol) and str(token) in self.operators:
#                 # It's an operator, pop two values and create new expression
#                 b = stack.pop()
#                 a = stack.pop()
#                 stack.append(hy.models.Expression([
#                     token,  # operator
#                     a,      # first operand
#                     b       # second operand
#                 ]))
#             else:
#                 # It's a value or time expression, push to stack
#                 stack.append(token)

#         return stack[0] if stack else None


#     def parse(self, expression: str) -> hy.models.Expression:
#         """Parse time expression into Hy expression"""
#         tokens = self.tokenize(expression)
#         expr = self.to_hy_expression(tokens)
#         return expr


#     def create_evaluation_context(self) -> dict:
#         """Create context with units and math functions"""
#         units = config.units
#         context = {
#             # Make units available by their labels
#             label: DecimalTimeLength(unit.value)
#             for label, unit in units.get_all_units().items()
#         }
#         # Add math functions and constants
#         context.update({
#             'math': math,
#             'sqrt': math.sqrt,
#             'abs': abs,
#             'pi': math.pi,
#             'e': math.e,
#         })
#         return context

#     def evaluate(self, expression: str) -> DecimalTimeLength:
#         """Parse and evaluate a time expression"""
#         hy_expr = self.parse(expression)
#         context = self.create_evaluation_context()
#         result = evaluate_hy_expression(hy_expr, context)
#         return result
