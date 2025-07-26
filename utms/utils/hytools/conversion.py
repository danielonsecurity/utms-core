from decimal import Decimal
from typing import Any
from datetime import datetime

import hy
from hy.models import Expression, Symbol, Integer, Float


def hy_to_python(data: Any) -> Any:
    """Convert Hy model objects to Python values.

    Args:
        value: Any value, potentially a Hy model object

    Returns:
        Equivalent Python value
    """
    if data is None:
        return None

    if isinstance(data, (hy.models.String, hy.models.Symbol)):
        return str(data)

    if isinstance(data, hy.models.Integer):
        return int(data)

    if isinstance(data, hy.models.Float):
        return float(data)

    if isinstance(data, hy.models.Keyword):
        # Convert :keyword to "keyword"
        return str(data)[1:]

    if isinstance(data, (hy.models.List, hy.models.Expression, list, tuple)):
        return [hy_to_python(item) for item in data]

    if isinstance(data, (hy.models.Dict, dict)):
        return {hy_to_python(k): hy_to_python(v) for k, v in data.items()}

    return data


def python_to_hy(value: Any) -> str:
    """Format a Python value as a Hy expression."""
    if value is None:
        return "None" # hy.repr(None) is 'None'
    if isinstance(value, bool):
        return hy.repr(hy.models.Boolean(value)) # '#t' or '#f'
    if isinstance(value, int):
        return hy.repr(hy.models.Integer(value))
    if isinstance(value, float):
        return hy.repr(hy.models.Float(value))
    if isinstance(value, str):
        return hy.repr(hy.models.String(value)) # Adds quotes: "abc"
    if isinstance(value, list):
        items_as_hy_models = []
        for item in value:
            if isinstance(item, str): items_as_hy_models.append(hy.models.String(item))
            elif isinstance(item, int): items_as_hy_models.append(hy.models.Integer(item))
            elif isinstance(item, bool): items_as_hy_models.append(hy.models.Boolean(item))
            elif item is None: items_as_hy_models.append(None) # Hy List can contain Python None, hy.repr handles
            else: items_as_hy_models.append(hy.models.String(str(item))) # Fallback: repr as string
        return hy.repr(hy.models.List(items_as_hy_models))
    if isinstance(value, dict):
        hy_dict_pairs = []
        for k, v in value.items():
            hy_dict_pairs.append(hy.models.Keyword(str(k))) # Assume keys become keywords
            if isinstance(v, str): hy_dict_pairs.append(hy.models.String(v))
            elif isinstance(v, int): hy_dict_pairs.append(hy.models.Integer(v))
            else: hy_dict_pairs.append(hy.models.String(str(v)))
        return hy.repr(hy.models.Dict(hy_dict_pairs))
    
    if isinstance(value, hy.models.Object):
        return hy.repr(value)
    return str(value)


def list_to_dict(flat_list):
    return dict(zip(flat_list[::2], flat_list[1::2]))

def py_list_to_hy_expression(py_list: list) -> Expression:
    """
    Recursively converts a Python list that represents an S-expression back into a
    fully-formed hy.models.Expression object.

    This is the counterpart to hy_to_python for executable code, turning names
    into Symbols, not Strings.
    e.g., ['current-time'] -> Expression([Symbol('current-time')])
    """
    elements = []
    for item in py_list:
        if isinstance(item, list):
            elements.append(py_list_to_hy_expression(item))
        elif isinstance(item, str):
            # Treat strings as names to be looked up (Symbols)
            elements.append(Symbol(item))
        elif isinstance(item, int):
            elements.append(Integer(item))
        elif isinstance(item, float):
            elements.append(Float(item))
        elif isinstance(item, bool):
            elements.append(bool(item))
        else:
            # For other types like None, let them pass through.
            elements.append(item)
    return Expression(elements)

def python_to_hy_model(value: Any) -> hy.models.Object:
    """
    Recursively converts a Python object into a corresponding hy.models object.
    """
    if isinstance(value, datetime):
        return hy.models.Expression([
            hy.models.Symbol("datetime"),
            hy.models.Integer(value.year),
            hy.models.Integer(value.month),
            hy.models.Integer(value.day),
            hy.models.Integer(value.hour),
            hy.models.Integer(value.minute),
            hy.models.Integer(value.second),
            hy.models.Integer(value.microsecond)
        ])
    
    if isinstance(value, dict):
        pairs = []
        for k, v in value.items():
            # Keys in a Hy dict are typically keywords
            pairs.append(hy.models.Keyword(str(k)))
            # Recursively convert the value
            pairs.append(python_to_hy_model(v))
        return hy.models.Dict(pairs)
    
    if isinstance(value, list):
        if not value:
            return hy.models.Expression([])

        # Assume lists are function calls for actions
        function_symbol = hy.models.Symbol(str(value[0]))
        args = [python_to_hy_model(item) for item in value[1:]]
        return hy.models.Expression([function_symbol] + args)

    if isinstance(value, str):
        if value.lower() == 'true':
            return hy.models.Symbol('True')
        if value.lower() == 'false':
            return hy.models.Symbol('False')
        return hy.models.String(value)

    if isinstance(value, bool):
        return hy.models.Symbol('True') if value else hy.models.Symbol('False')
    
    if isinstance(value, int):
        return hy.models.Integer(value)

    if isinstance(value, float):
        return hy.models.Float(value)

    if value is None:
        return hy.models.Symbol('None')
        
    return hy.models.String(str(value))
