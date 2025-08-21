# tests/core/hy/test_converter.py

import pytest
from datetime import datetime
import hy
from utms.core.hy.converter import converter, py_list_to_hy_expression

# --- Test Case 1: The agent-state Bug ---
# We need to convert a rich Python object into a proper Hy AST model.
def test_py_to_model_for_agent_state():
    """
    Tests that a Python list containing a dict with a datetime (like agent-state)
    is correctly converted to a hy.models.List containing a hy.models.Dict.
    """
    # Arrange: This is the correct Python data the agent works with.
    python_data = [{
        'cursors': {
            'recurrence': datetime(2025, 8, 20, 12, 30, 0)
        }
    }]

    # Act: Convert it to a Hy AST model.
    result_model = converter.py_to_model(python_data)

    # Assert: Check the structure and string representation.
    assert isinstance(result_model, hy.models.List)
    assert len(result_model) == 1
    assert isinstance(result_model[0], hy.models.Dict)
    
    # The string representation is the ultimate proof.
    expected_string = '[{:cursors {:recurrence (datetime 2025 8 20 12 30 0 0)}}]'
    assert converter.model_to_string(result_model) == expected_string


# --- Test Case 2: The on-recurrence-hook Bug ---
# We need to serialize a Python list representing CODE back into an executable Hy expression.
def test_py_list_to_hy_expression_for_code():
    """
    Tests that the specialist `py_list_to_hy_expression` function correctly
    converts a Python list representing code into a hy.models.Expression `(...)`.
    """
    # Arrange: This is the Python list representing our hook.
    python_code_list = ['quote', ['notify', 'thinkpad', 'Lunch Time']]

    # Act: Convert it using the specialist tool for code.
    result_model = py_list_to_hy_expression(python_code_list)

    # Assert: The result must be an Expression, not a List.
    assert isinstance(result_model, hy.models.Expression)
    
    # The string representation must use parentheses, not square brackets.
    expected_string = '(quote (notify "thinkpad" "Lunch Time"))'
    assert converter.model_to_string(result_model) == expected_string


# --- Test Case 3: Deserialization ---
# We need to ensure that when we read a Hy AST Model, it becomes a rich Python object.
def test_model_to_py_for_agent_state():
    """
    Tests that a Hy AST model for agent-state is correctly deserialized
    into a rich Python list of dictionaries, not a flat list.
    """
    # Arrange: This is the correct Hy AST model, as read from a file.
    hy_model = hy.models.List([
        hy.models.Dict([
            hy.models.Keyword('cursors'),
            hy.models.Dict([
                hy.models.Keyword('recurrence'),
                hy.models.Expression([
                    hy.models.Symbol('datetime'), hy.models.Integer(2025),
                    hy.models.Integer(8), hy.models.Integer(20)
                ])
            ])
        ])
    ])

    # Act: Convert it to a Python object using the rich deserializer.
    python_result = converter.model_to_py(hy_model)

    # Assert: Check the structure and content.
    assert isinstance(python_result, list)
    assert isinstance(python_result[0], dict)
    assert 'cursors' in python_result[0]
    assert isinstance(python_result[0]['cursors']['recurrence'], datetime)
