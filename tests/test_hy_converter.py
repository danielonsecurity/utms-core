import pytest
from datetime import datetime
from decimal import Decimal
import hy
from utms.core.hy.converter import converter, py_list_to_hy_expression

# --- Group 1: Python to Hy Model (`py_to_model`) ---

def test_py_to_model_handles_nested_dicts_and_lists():
    """Tests conversion of a complex Python object with nested structures."""
    python_data = {
        'level1_key': 'level1_value',
        'level1_list': [1, True, None, "a_string"],
        'level1_dict': {
            'level2_key': datetime(2025, 1, 1),
            'level2_decimal': Decimal("10.5")
        }
    }
    model = converter.py_to_model(python_data)

    assert isinstance(model, hy.models.Dict)
    # A simple way to verify is to convert back to a string
    expected_hy_string = ('{:level1_key "level1_value" '
                          ':level1_list [1 True None "a_string"] '
                          ':level1_dict {:level2_key (datetime 2025 1 1 0 0 0 0) '
                          ':level2_decimal (Decimal "10.5")}}')
    assert converter.model_to_string(model) == expected_hy_string

def test_py_to_model_is_idempotent():
    """Tests that passing an existing hy model to py_to_model returns it unchanged."""
    model = hy.models.String("hello")
    assert converter.py_to_model(model) is model

def test_py_list_to_hy_expression_for_code():
    """Tests the specialist function for converting a Python list representing code."""
    python_code_list = ['quote', ['notify', 'thinkpad', 'Lunch Time']]
    result_model = py_list_to_hy_expression(python_code_list)
    assert isinstance(result_model, hy.models.Expression)
    expected_string = '(quote (notify "thinkpad" "Lunch Time"))'
    assert converter.model_to_string(result_model) == expected_string


# --- Group 2: Hy Model to Python (`model_to_py`) ---

def test_model_to_py_handles_nested_models():
    """Tests conversion of a complex Hy AST into a rich Python object."""
    model = list(hy.read_many("""
        {:level1_key "level1_value"
         :level1_list [1 True None "a_string"]
         :level1_dict {:level2_key (datetime 2025 1 1)
                       :level2_decimal (Decimal "10.5")}}
    """))[0]
    
    python_obj = converter.model_to_py(model)

    expected_python_obj = {
        'level1_key': 'level1_value',
        'level1_list': [1, True, None, 'a_string'],
        'level1_dict': {
            'level2_key': datetime(2025, 1, 1),
            'level2_decimal': Decimal("10.5")
        }
    }
    assert python_obj == expected_python_obj
    assert isinstance(python_obj['level1_dict']['level2_key'], datetime)

def test_model_to_py_handles_raw_conversion():
    """Tests the `raw=True` flag, which should convert everything to basic types."""
    model = list(hy.read_many("""
        {:key (datetime 2025 1 1)}
    """))[0]

    # `raw=True` gives a flat list of key-value pairs
    raw_list = converter.model_to_py(model, raw=True)
    expected_raw_list = ['key', ['datetime', 2025, 1, 1]]
    assert raw_list == expected_raw_list

# --- Group 3: The Hybrid Object Bug and Edge Cases (Most Important) ---

def test_model_to_py_handles_hybrid_list_of_dicts_with_keyword_keys():
    """
    THE CORE BUG TEST: Tests conversion of a Python list containing Python dicts
    that incorrectly use `hy.models.Keyword` as keys.
    """
    hybrid_object = [  # Python list
        {  # Python dict
            hy.models.Keyword('start_time'): datetime(2025, 8, 27, 10, 0, 0),
            hy.models.Keyword('notes'): hy.models.String("A test note.")
        }
    ]

    python_result = converter.model_to_py(hybrid_object)

    # Assert the output is a PURE Python object
    assert isinstance(python_result, list)
    first_item = python_result[0]
    assert isinstance(first_item, dict)
    
    # Assert keys are now strings
    assert 'start_time' in first_item
    assert all(isinstance(k, str) for k in first_item.keys())

    # Assert values were also converted
    assert isinstance(first_item['start_time'], datetime)
    assert isinstance(first_item['notes'], str)
    assert first_item['notes'] == "A test note."


def test_model_to_py_handles_deeply_nested_hybrid_objects():
    """
    Tests a more complex hybrid object to ensure conversion is recursive.
    """
    hybrid_object = { # Python dict
        hy.models.Keyword('level1_key'): [ # Python list
            { # Python dict
                hy.models.Keyword('level2_key'): hy.models.Expression([
                    hy.models.Symbol('datetime'), hy.models.Integer(2025)
                ])
            }
        ]
    }

    python_result = converter.model_to_py(hybrid_object)

    assert isinstance(python_result, dict)
    assert 'level1_key' in python_result
    assert all(isinstance(k, str) for k in python_result.keys())
    
    level1_value = python_result['level1_key']
    assert isinstance(level1_value, list)
    
    level2_dict = level1_value[0]
    assert isinstance(level2_dict, dict)
    assert 'level2_key' in level2_dict
    assert all(isinstance(k, str) for k in level2_dict.keys())
    
    # Check that the Expression inside was also converted
    assert level2_dict['level2_key'] == ['datetime', 2025]


def test_model_to_py_handles_empty_structures():
    """Ensures empty lists and dicts are handled correctly."""
    assert converter.model_to_py([]) == []
    assert converter.model_to_py({}) == {}
    assert converter.model_to_py(hy.models.List()) == []
    assert converter.model_to_py(hy.models.Dict()) == {}


def test_model_to_py_is_idempotent_with_pure_python_objects():
    """Ensures that passing an already-clean Python object doesn't change it."""
    clean_object = [{'key': 'value', 'time': datetime(2025, 1, 1)}]
    result = converter.model_to_py(clean_object)
    assert result == clean_object
    assert result[0] == clean_object[0]    
