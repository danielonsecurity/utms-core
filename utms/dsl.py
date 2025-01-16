import logging
from datetime import datetime
from decimal import Decimal

from lark import Lark, Token, Transformer, Tree, logger, v_args

logger.setLevel(logging.DEBUG)


class DSLTransformer(Transformer):
    variables = {}

    def start(self, expression):
        return {"start": expression}

    def units(self, data):
        return data

    def unit(self, data):
        fields_dict = {}
        for field in data[1:]:
            fields_dict.update(field[0])
        return {data[0].value[1:-1]: fields_dict}

    def field(self, field):
        return field

    def length(self, number):
        self.variables["length"] = number[0]
        return {"length": number[0]}

    def timezone(self, data):
        self.variables["timezone"] = Decimal(data[0].value)
        return {"timezone": Decimal(data[0].value)}

    def start_field(self, expression):
        return {"start": expression}

    def names(self, data):
        return {"names": [name.value[1:-1] for name in data]}

    def term(self, children):
        return Decimal(children[0])

    def add(self, children):
        left, right = children
        return left + right

    def sub(self, children):
        left, right = children
        return left - right

    def mul(self, children):
        left, right = children
        return left * right

    def div(self, children):
        left, right = children
        return left / right

    def divint(self, children):
        left, right = children
        return left // right

    def rest(self, children):
        left, right = children
        return left % right

    def expression(self, children):
        if isinstance(children[0], Decimal):
            return children[0]

    def factor(self, children):
        if isinstance(children[0], Token):
            return Decimal(children[0].value)
        elif isinstance(children[0], Decimal):
            return children[0]

    def keyword(self, tree):
        if tree[0].data.value == "input_keyword":
            return Decimal(1736847493)
            # return Decimal(input("input="))

        if tree[0].data.value == "length_keyword":
            return self.variables["length"]
        if tree[0].data.value == "timezone_keyword":
            return self.variables["timezone"]

    def assignment(self, data):
        var_name = data[0].value
        expression = data[1]
        self.variables[var_name] = expression
        return (var_name, expression)

    def block(self, tree):
        return tree[-1]

    def variable(self, data):
        name = data[0].value
        if name in self.variables:
            return self.variables[name]
        return data[0]


def debug_tokens(parser, dsl_content):
    for token in parser.lex(dsl_content):
        print(f"Token: {token.type} {token.value}")


# Load the grammar
dsl_grammar = open("resources/unit_grammar.lark").read()

# Creating the parser with the updated grammar
parser = Lark(dsl_grammar, parser="lalr", transformer=DSLTransformer(), debug=True, start="units")

# Parse the DSL file
with open("resources/units.utms", "r") as file:
    dsl_content = file.read()
    # debug_tokens(parser, dsl_content)

# Parse the DSL content
parsed_units = parser.parse(dsl_content)
units = {key: value for d in parsed_units for key, value in d.items()}
print(f"Parsed Units: {parsed_units}")

for unit in units.keys():
    print(unit)
    timestamp = int(units[unit]["start"][0])
    print(datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S"))
