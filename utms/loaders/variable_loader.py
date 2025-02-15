import os
import hy
from typing import Any, Dict, Optional

from utms.utms_types.hy.types import HyProperty

from ..core.anchors import Anchor, AnchorConfig
from ..resolvers import VariableResolver, evaluate_hy_file
from ..utils import get_logger
from ..utms_types import (
    AnchorKwargs,
    ExpressionList,
    HyExpression,
    LocalsDict,
    ResolvedValue,
    is_expression,
)
from ..core.variables import VariableManager

logger = get_logger("core.anchor.variable_loader")

_resolver = VariableResolver()


def parse_variable_definitions(variable_data: ExpressionList) -> Dict[str, dict]:
    """Parse Hy variable definitions into a dictionary."""
    variables = {}
    logger.debug("Starting to parse variable definitions")

    for var_def_expr in variable_data:
        if not is_expression(var_def_expr):
            logger.debug("Skipping non-Expression: %s", var_def_expr)
            continue

        if str(var_def_expr[0]) != "def-var":
            logger.debug("Skipping non-def-var expression: %s", var_def_expr[0])
            continue

        _, var_name_sym, var_value = var_def_expr
        var_name = str(var_name_sym)
        logger.debug("Processing variable: %s", var_name)

        variables[var_name] = {"name": var_name, "value": HyProperty(value=var_value,
                                                                     original=hy.repr(var_value))}

    return variables


def initialize_variables(parsed_vars: Dict[str, dict]) -> VariableManager:
    """Create resolved variables from parsed definitions."""
    manager = VariableManager()
    for var_name, var_info in parsed_vars.items():
        var_property = var_info["value"]
        resolved_value = _resolver.resolve(var_property.value)
        original = var_property.original.strip("'") if var_property.original else None
        manager.add_variable(name=var_name,
                             value=resolved_value,
                             original=original)
        _resolver._resolved_vars[var_name] = resolved_value
    return manager


def process_variables(variable_data: ExpressionList) -> Dict[str, Any]:
    """Process Hy variable definitions into resolved variables."""
    logger.debug("Starting process_variables")
    parsed_vars = parse_variable_definitions(variable_data)
    logger.debug("Parsed variables: %s", list(parsed_vars.keys()))
    variable_manager = initialize_variables(parsed_vars)
    logger.debug("Initialized variables: %s", list(variable_manager.resolved_vars.keys()))
    return variable_manager
