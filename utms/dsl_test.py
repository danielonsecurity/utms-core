turtle_grammar = """
start: instruction+
 
instruction: MOVEMENT NUMBER            -> movement
           | "c" COLOR [COLOR]          -> change_color
           | "fill" code_block          -> fill
           | "repeat" NUMBER code_block -> repeat
 
code_block: "{" instruction+ "}"
 
MOVEMENT: "f"|"b"|"l"|"r"
COLOR: LETTER+
 
%import common.LETTER
%import common.INT -> NUMBER
%import common.WS
%ignore WS
"""

text = """
c red yellow
fill { repeat 36 {
    f200 l170
}}
"""
 
from lark import Lark
parser = Lark(turtle_grammar)  # Scannerless Earley is the default
 
print(parser.parse(text).pretty())
