# tests/core/hy/test_resolver.py

import pytest
from datetime import datetime
from decimal import Decimal
import hy

# We need to import the actual classes, not just instances.
from utms.core.hy.resolvers.base import HyResolver
from utms.core.managers.elements.entity import EntityManager
from utms.core.components.elements.entity import EntityComponent

# --- Test Fixtures ---

@pytest.fixture
def base_resolver():
    """Provides a basic HyResolver instance."""
    return HyResolver()

@pytest.fixture
def entity_resolver():
    """Provides an EntityResolver instance with mock dependencies."""
    # Mocks for dependencies that the resolver needs.
    # In a real-world scenario, you might use more sophisticated mocks (e.g., pytest-mock).
    class MockEntityManager:
        def get(self, key): return None
    class MockEntityComponent:
        pass
    
    return HyResolver(MockEntityManager(), MockEntityComponent()) # HyResolver can be used as a base for entity tests
                                                                 # since EntityResolver adds functions but doesn't change core logic
                                                                 # We should switch to EntityResolver if we test its specific functions.

# --- Group 1: Basic Type Conversion Tests ---

def test_resolver_returns_basic_python_types_unchanged(base_resolver):
    """Ensures that standard Python types are passed through correctly."""
    assert base_resolver.resolve("hello")[0] == "hello"
    assert base_resolver.resolve(123)[0] == 123
    assert base_resolver.resolve(True)[0] is True
    assert base_resolver.resolve(None)[0] is None

def test_resolver_converts_hy_primitives_to_python_primitives(base_resolver):
    """
    This test enforces the contract: Hy primitive models MUST be converted
    to their corresponding pure Python types.
    """
    assert base_resolver.resolve(hy.models.String("hello"))[0] == "hello"
    assert base_resolver.resolve(hy.models.Integer(42))[0] == 42
    assert base_resolver.resolve(hy.models.Float(3.14))[0] == 3.14
    assert base_resolver.resolve(hy.models.Keyword("a-keyword"))[0] == "a-keyword"
    assert base_resolver.resolve(hy.models.Symbol("True"))[0] is True
    assert base_resolver.resolve(hy.models.Symbol("None"))[0] is None

# --- Group 2: The Core Bug - Data Structure Conversion ---

def test_resolver_converts_hylist_to_python_list(base_resolver):
    """Tests that a HyList containing primitives is converted to a Python list."""
    hy_list = hy.models.List([
        hy.models.Integer(1),
        hy.models.String("two"),
        hy.models.Symbol("True")
    ])
    result = base_resolver.resolve(hy_list)[0]
    assert result == [1, "two", True]
    assert isinstance(result, list)

def test_resolver_converts_hydict_to_python_dict_with_string_keys(base_resolver):
    """
    THE MOST IMPORTANT TEST.
    This test proves that a HyDict is converted to a Python dict,
    and its keys (which are often HyKeywords) are converted to Python strings.
    """
    hy_dict = hy.models.Dict([
        hy.models.Keyword("str-key"), hy.models.String("value1"),
        hy.models.Keyword("int-key"), hy.models.Integer(123)
    ])
    result = base_resolver.resolve(hy_dict)[0]

    expected_dict = {
        "str-key": "value1",
        "int-key": 123
    }
    assert result == expected_dict
    assert isinstance(result, dict)
    assert all(isinstance(k, str) for k in result.keys())

def test_resolver_converts_nested_hy_structures_to_pure_python(base_resolver):
    """
    A comprehensive test for deep conversion. The entire resolved structure
    must be free of any hy.models objects.
    """
    model = list(hy.read_many("""
        [
            {:key "value"}
            {:nested {:a 1}}
        ]
    """))[0]
    
    result = base_resolver.resolve(model)[0]
    
    expected_result = [
        {"key": "value"},
        {"nested": {"a": 1}}
    ]
    
    assert result == expected_result
    # Verify types recursively
    assert isinstance(result, list)
    assert isinstance(result[0], dict)
    assert isinstance(list(result[0].keys())[0], str)
    assert isinstance(result[1]['nested'], dict)

# --- Group 3: Expression Evaluation ---

def test_resolver_evaluates_simple_expression(base_resolver):
    """Tests that a simple expression like (+ 1 2) is executed."""
    expr = hy.models.Expression([hy.models.Symbol("+"), hy.models.Integer(1), hy.models.Integer(2)])
    result = base_resolver.resolve(expr)[0]
    assert result == 3

def test_resolver_evaluates_expression_within_data_structure(base_resolver):
    """
    Tests that expressions nested inside lists or dicts are evaluated,
    and the final structure is pure Python.
    """
    model = list(hy.read_many("""
        { :a (+ 10 20)
          :b [1 2 (* 3 4)] }
    """))[0]

    result = base_resolver.resolve(model)[0]

    expected_result = {
        "a": 30,
        "b": [1, 2, 12]
    }
    assert result == expected_result
    assert isinstance(result, dict)
    assert isinstance(result['b'], list)
