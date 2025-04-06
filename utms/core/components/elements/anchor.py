import os
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

from utms.core.hy.ast import HyAST
from utms.utils import hy_to_python

from utms.core.formats import TimeUncertainty
from utms.core.loaders.elements.anchor import AnchorLoader
from utms.core.loaders.base import LoaderContext
from utms.core.managers.elements.anchor import AnchorManager
from utms.core.models.anchor import Anchor, FormatSpec
from utms.core.components.base import SystemComponent


class AnchorComponent(SystemComponent):
    """Component managing anchors."""

    def __init__(self, config_dir: str, component_manager=None):
        super().__init__(config_dir, component_manager)
        self._ast_manager = HyAST()
        self._anchor_manager = AnchorManager()
        self._loader = AnchorLoader(self._anchor_manager)

    def load(self) -> None:
        """Load anchors from anchors.hy"""
        if self._loaded:
            return

        anchors_file = os.path.join(self._config_dir, "anchors.hy")
        if os.path.exists(anchors_file):
            try:
                # Get variables from variables component
                variables_component = self.get_component("variables")

                # Get resolved variable values
                variables = {}
                for name, var in variables_component.items():
                    try:
                        variables[name] = hy_to_python(var.value)
                        # Also add underscore version for compatibility
                        variables[name.replace("-", "_")] = hy_to_python(var.value)
                    except Exception as e:
                        self.logger.error(f"Error converting variable {name}: {e}")

                self.logger.debug(f"Available variables: {variables}")

                # Parse file into nodes
                nodes = self._ast_manager.parse_file(anchors_file)

                # Create context with variables
                context = LoaderContext(config_dir=self._config_dir, variables=variables)

                # Process nodes using loader
                self._items = self._loader.process(nodes, context)

                self._loaded = True

            except Exception as e:
                self.logger.error(f"Error loading anchors: {e}")
                raise

    def save(self) -> None:
        """Save anchors to anchors.hy"""
        anchors_file = os.path.join(self._config_dir, "anchors.hy")
        self._anchor_manager.save(anchors_file)

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
