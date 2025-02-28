from typing import Any, Dict, List, Optional

from utms.core.hy.ast import HyAST, HyNode
from utms.utms_types import HyProperty
from utms.core.mixins.manager import ManagerMixin
from utms.core.models.variable import Variable
from .base import BaseManager


class VariableManager(BaseManager[Variable]):
    """Manages variables with their values and original expressions."""

    def __init__(self) -> None:
        super().__init__()
        self._resolved_vars: Dict[str, Any] = {}

    def create(self, label: str, value: Any, original: Optional[str] = None) -> Variable:
        """Create a new variable."""
        variable = Variable(name=label, property=HyProperty(value=value, original=original))
        self._items[label] = variable
        self._resolved_vars[label] = value
        return variable

    def get_value(self, name: str) -> Optional[Any]:
        """Get just the resolved value of a variable."""
        return self._resolved_vars.get(name)

    @property
    def resolved_vars(self) -> Dict[str, Any]:
        """Access to resolved variables."""
        return dict(self._resolved_vars)

    def serialize(self) -> Dict[str, Any]:
        """Convert variables to serializable format."""
        return {
            name: {"value": var.value, "original": var.original}
            for name, var in self._items.items()
        }

    def deserialize(self, data: Dict[str, Any]) -> None:
        """Load variables from serialized data."""
        self.clear()
        for name, var_data in data.items():
            self.create(label=name, value=var_data["value"], original=var_data.get("original"))
        self._initialized = True

    def _data_to_nodes(self, data: Dict[str, Any]) -> List[HyNode]:
        """Convert serialized data to Hy nodes."""
        nodes = []
        for name, var_data in data.items():
            node = HyNode(
                type="def-var",
                value=name,
                children=[
                    HyNode(
                        type="value",
                        value=var_data["value"],
                        original=var_data.get("original"),
                        is_dynamic=bool(var_data.get("original")),
                    )
                ],
            )
            nodes.append(node)
        return nodes

    def _nodes_to_data(self, nodes: List[HyNode]) -> Dict[str, Any]:
        """Convert Hy nodes to serializable data."""
        data = {}
        for node in nodes:
            if node.type != "def-var":
                continue

            name = node.value
            if node.children and len(node.children) > 0:
                value_node = node.children[0]
                data[name] = {"value": value_node.value, "original": value_node.original}
        return data
