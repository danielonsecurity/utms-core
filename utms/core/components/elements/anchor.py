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


class AnchorComponent(SystemComponent):
    """Component managing anchors."""

    def __init__(self, config_dir: str, component_manager=None):
        super().__init__(config_dir, component_manager)
        self._ast_manager = HyAST()
        self._anchor_manager = AnchorManager()
        self._loader = AnchorLoader(self._anchor_manager)
        self._anchors_dir = os.path.join(self._config_dir, "anchors")

    def load(self) -> None:
        """Load anchors from all Hy files in the anchors directory"""
        if self._loaded:
            return

        if not os.path.exists(self._anchors_dir):
            os.makedirs(self._anchors_dir)
        try:
            variables_component = self.get_component("variables")

            variables = {}
            if variables_component:
                for name, var in variables_component.items():
                    try:
                        variables[name] = converter.model_to_py(var.value, raw=True)
                        variables[name.replace("-", "_")] = converter.model_to_py(var.value, raw=True)
                    except Exception as e:
                        self.logger.error(f"Error converting variable {name}: {e}")
                self.logger.debug(f"Available variables: {variables}")

            context = LoaderContext(config_dir=self._config_dir, variables=variables)

            all_items = {}

            anchor_files = [f for f in os.listdir(self._anchors_dir) if f.endswith(".hy")]

            if not anchor_files:
                self._loaded = True
                return

            for filename in anchor_files:
                file_path = os.path.join(self._anchors_dir, filename)
                self.logger.debug(f"Loading anchors from {file_path}")

                try:
                    nodes = self._ast_manager.parse_file(file_path)
                    items = self._loader.process(nodes, context)
                    all_items.update(items)
                except Exception as e:
                    self.logger.error(f"Error loading anchors from {file_path}: {e}")

            self._items = all_items
            self._loaded = True

        except Exception as e:
            self.logger.error(f"Error loading anchors: {e}")
            raise

    def save(self) -> None:
        """Save anchors to appropriate files in the anchors directory"""
        if not os.path.exists(self._anchors_dir):
            os.makedirs(self._anchors_dir)

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
            file_path = os.path.join(self._anchors_dir, f"{category}.hy")

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
