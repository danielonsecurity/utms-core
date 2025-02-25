import os
from typing import Any, Dict, Type

import appdirs

from ..utils import get_logger
from . import constants
from .components.anchor import AnchorComponent
from .components.base import ComponentManager, SystemComponent
from .components.fixed_units import FixedUnitComponent
from .components.patterns import PatternComponent
from .components.variables import VariableComponent

logger = get_logger("core.new_config")


class NewConfig:
    """New configuration class using component-based system"""

    def __init__(self):
        # Initialize config directory
        self._utms_dir = appdirs.user_config_dir(constants.APP_NAME, constants.COMPANY_NAME)
        os.makedirs(self.utms_dir, exist_ok=True)

        # Initialize component manager
        self._component_manager = ComponentManager(self._utms_dir)

        # Register components without loading them
        self._register_components()

    def _register_components(self):
        """Register all available components"""
        self._component_manager.register("patterns", PatternComponent)
        self._component_manager.register("variables", VariableComponent)
        self._component_manager.register("units", FixedUnitComponent)
        self._component_manager.register("anchors", AnchorComponent)
        # self._component_manager.register("units", UnitComponent)
        # self._component_manager.register("anchors", AnchorComponent)
        # etc...
        pass

    @property
    def utms_dir(self) -> str:
        """Get UTMS configuration directory"""
        return str(self._utms_dir)

    def get_component(self, name: str) -> SystemComponent:
        """Get a component by name, loading it if necessary"""
        return self._component_manager.get(name)

    @property
    def patterns(self) -> PatternComponent:
        return self.get_component("patterns")

    @property
    def variables(self) -> VariableComponent:
        return self.get_component("variables")

    @property
    def units(self) -> FixedUnitComponent:
        return self.get_component("units")

    @property
    def anchors(self) -> AnchorComponent:
        return self.get_component("anchors")

    # Properties for backward compatibility
    # These will be added as we migrate each component
    # @property
    # def variables(self):
    #     return self.get_component("variables")

    # @property
    # def units(self):
    #     return self.get_component("units")

    # etc...
