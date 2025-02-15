from dataclasses import dataclass
from typing import Any, Dict, Optional

from ..utils import get_logger
from ..utms_types import HyProperty
from ..resolvers import HyAST, HyNode

logger = get_logger("core.variables")


class VariableManager:
    """Manages variables with their values and original expressions."""
    
    def __init__(self) -> None:
        self._variables: Dict[str, HyProperty] = {}
        self._resolved_vars: Dict[str, Any] = {}

    def add_variable(self, name: str, value: Any, original: Optional[str] = None) -> None:
        """Add a variable with both its resolved value and original expression."""
        self._variables[name] = HyProperty(value=value, original=original)
        self._resolved_vars[name] = value

    def get_variable(self, name: str) -> Optional[HyProperty]:
        """Get the variable's HyProperty if it exists."""
        return self._variables.get(name)

    def get_value(self, name: str) -> Optional[Any]:
        """Get just the resolved value of a variable."""
        return self._resolved_vars.get(name)

    @property
    def resolved_vars(self) -> Dict[str, Any]:
        """Access to resolved variables for backward compatibility."""
        return self._resolved_vars

    def save(self, filename: str) -> None:
        """Save variables to Hy file."""
        ast_manager = HyAST()
        nodes = []
        for name, prop in self._variables.items():
            node = HyNode(
                type="def-var",
                value=name,
                children=[
                    HyNode(
                        type="value",
                        value=prop.value,
                        original=prop.original,
                        is_dynamic=bool(prop.original)
                    )
                ]
            )
            nodes.append(node)

        breakpoint()
        with open(filename, "w") as f:
            f.write(ast_manager.to_hy(nodes))
    
