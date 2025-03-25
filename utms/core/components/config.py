from pathlib import Path
from typing import Any, Dict

from utms.core.components.base import SystemComponent
from utms.core.hy.ast import HyAST
from utms.core.plugins import plugin_registry


class ConfigComponent(SystemComponent):
    """Component managing UTMS configuration"""

    def __init__(self, config_dir: str, component_manager=None):
        super().__init__(config_dir, component_manager)
        self._ast_manager = HyAST()

    def load(self) -> None:
        """Load configuration from config.hy"""
        if self._loaded:
            return

        config_file = Path(self._config_dir) / "config.hy"
        self.logger.debug(f"Loading config from: {config_file}")

        try:
            nodes = self._ast_manager.parse_file(str(config_file))
            if nodes:
                # Assuming first node is config
                config_node = nodes[0]
                self._items = self._node_to_dict(config_node)
                self.logger.debug(f"Loaded config: {self._items}")
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            raise

        self._loaded = True

    def save(self) -> None:
        """Save configuration to config.hy"""
        config_file = Path(self._config_dir) / "config.hy"

        # Get the config plugin
        plugin = plugin_registry.get_node_plugin("custom-set-config")
        if not plugin:
            raise ValueError("Config plugin not found")

        # Create config node from current items
        config_node = self._dict_to_node(self._items)

        # Convert to Hy code and save
        content = self._ast_manager.to_hy([config_node])
        with open(config_file, "w") as f:
            f.write(content)

    def _node_to_dict(self, node: "HyNode") -> Dict[str, Any]:
        """Convert config node to dictionary"""
        result = {}
        for setting in node.children:
            key = setting.value
            value = setting.children[0].value
            result[key] = value
        return result

    def _dict_to_node(self, data: Dict[str, Any]) -> "HyNode":
        """Convert dictionary to config node"""
        plugin = plugin_registry.get_node_plugin("custom-set-config")
        if not plugin:
            raise ValueError("Config plugin not found")

        # Create a minimal expression for the plugin to parse
        expr = hy.models.Expression(
            [
                hy.models.Symbol("custom-set-config"),
                *[hy.models.Expression([hy.models.Symbol(k), v]) for k, v in data.items()],
            ]
        )

        return plugin.parse(expr)
