import os
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

from utms.core.components.base import SystemComponent
from utms.core.formats import TimeUncertainty
from utms.core.hy.ast import HyAST
from utms.core.loaders.base import LoaderContext
from utms.core.loaders.elements.anchor import AnchorLoader
from utms.core.managers.elements.anchor import AnchorManager
from utms.core.models import Anchor, FormatSpec
from utms.core.hy.converter import converter
from utms.core.loaders.base import LoaderContext
from utms.utms_types.field.types import TypedValue

class AnchorComponent(SystemComponent):
    """Component managing anchors."""

    def __init__(self, config_dir: str, component_manager=None):
        super().__init__(config_dir, component_manager)
        self._ast_manager = HyAST()
        self._anchor_manager = AnchorManager()
        self._loader = AnchorLoader(self._anchor_manager)

        self._global_anchors_dir = os.path.join(self._config_dir, "global", "anchors")
        
        config_component = self.get_component("config")
        if not config_component.is_loaded(): config_component.load()
        active_user_config = config_component.get_config("active-user")

        self._user_anchors_dir = None
        if active_user_config and (active_user := active_user_config.get_value()):
            user_root = os.path.join(self._config_dir, "users", active_user)
            self._user_anchors_dir = os.path.join(user_root, "anchors")
        else:
            self.logger.warning("No active user; only global anchors will be loaded.")

    def load(self) -> None:
        """Load anchors from global and then user directories."""
        if self._loaded:
            return
            
        def _process_dir(path, context):
            if not (path and os.path.isdir(path)):
                return
            os.makedirs(path, exist_ok=True) 
            for filename in os.listdir(path):
                if not filename.endswith(".hy"): continue
                file_path = os.path.join(path, filename)
                try:
                    nodes = self._ast_manager.parse_file(file_path)
                    
                    self._loader.process(nodes, context)
                except Exception as e:
                    self.logger.error(f"Error loading anchors from {file_path}: {e}")
        
        self._anchor_manager.clear()
        self._items = self._anchor_manager.get_all()
        

        variables_component = self.get_component("variables")
        variables = {}
        if variables_component:
            for name, var_model in variables_component.items():
                if hasattr(var_model, 'value') and isinstance(var_model.value, TypedValue):
                    py_value = var_model.value.value
                    variables[name] = py_value
                    if '-' in name:
                        variables[name.replace('-', '_')] = py_value
        context = LoaderContext(config_dir=self._config_dir, variables=variables)

        _process_dir(self._global_anchors_dir, context)
        _process_dir(self._user_anchors_dir, context)

        self._loaded = True

    def save(self) -> None:
        """Save anchors to appropriate files in the anchors directory"""
        if not self._user_anchors_dir:
            self.logger.error("Cannot save anchors: No active user directory is configured.")
            return

        os.makedirs(self._user_anchors_dir, exist_ok=True)

        plugin = plugin_registry.get_node_plugin("def-anchor")
        if not plugin:
            raise ValueError("Anchor plugin not found")

        anchors_by_category = {}
        for key, anchor in self._items.items():
            category = getattr(anchor, "category", None)
            if not category:
                category = "default"

            if category not in anchors_by_category:
                anchors_by_category[category] = []
            anchors_by_category[category].append(anchor)

        for category, anchors in anchors_by_category.items():
            file_path = os.path.join(self._user_anchors_dir, f"{category}.hy")

            lines = []
            for anchor in sorted(anchors, key=lambda a: a.name):
                node = plugin.parse(["def-anchor", anchor.name, anchor.value])
                formatted_lines = plugin.format(node)
                lines.extend(formatted_lines)
                lines.append("")

            with open(file_path, "w") as f:
                f.write("\n".join(lines))

            self.logger.debug(f"Saved {len(anchors)} anchors to {file_path}")

    def create_anchor(
        self,
        label: str,
        name: str,
        value: Union[str, Decimal],
        formats: Optional[List[FormatSpec]] = None,
        groups: Optional[List[str]] = None,
        uncertainty: Optional[TimeUncertainty] = None,
    ) -> Anchor:
        """Create a new anchor."""
        return self._anchor_manager.create(
            label=label,
            name=name,
            value=value,
            formats=formats,
            groups=groups,
            uncertainty=uncertainty,
        )

    def get_anchor(self, label: str) -> Optional[Anchor]:
        """Get an anchor by label."""
        return self._anchor_manager.get(label)

    def get_anchors_by_group(self, group: str) -> List[Anchor]:
        """Get all anchors belonging to a specific group."""
        return self._anchor_manager.get_anchors_by_group(group)

    def get_anchors_by_groups(self, groups: List[str], match_all: bool = False) -> List[Anchor]:
        """Get anchors belonging to multiple groups."""
        return self._anchor_manager.get_anchors_by_groups(groups, match_all)

    def remove_anchor(self, label: str) -> None:
        """Remove an anchor by label."""
        self._anchor_manager.remove(label)
