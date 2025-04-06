import os

import appdirs

from utms.core.components.base import ComponentManager, SystemComponent
from utms.core.components.elements.anchor import AnchorComponent
from utms.core.components.elements.config import ConfigComponent
from utms.core.components.elements.fixed_unit import FixedUnitComponent
from utms.core.components.elements.pattern import PatternComponent
from utms.core.components.elements.variable import VariableComponent
from utms.core.logger import LoggerManager
from utms.core.mixins import LoggerMixin
from utms.core.plugins.discovery import discover_plugins
from utms.core.services.resource import ResourceService
from utms.utms_types import ConfigProtocol

from . import constants


class Config(ConfigProtocol, LoggerMixin):
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if not self._initialized:
            self.logger.debug("Initializing configuration")
            self._utms_dir = appdirs.user_config_dir(constants.APP_NAME, constants.COMPANY_NAME)
            os.makedirs(self.utms_dir, exist_ok=True)
            discover_plugins()

            self.logger.debug("Config directory %s", self.utms_dir)

            LoggerManager.configure_file_logging(self.utms_dir)

            self.logger.debug("Initializing component manager")
            self._component_manager = ComponentManager(self._utms_dir)

            self.logger.debug("Registering components")
            self._register_components()

            self._resource_manager = ResourceService(self._utms_dir)
            self._resource_manager.init_resources()

            if "loglevel" in self.config:
                LoggerManager.configure_from_config(self.config.get("loglevel"))

            self.__class__._initialized = True

    def _register_components(self):
        """Register all available components"""
        self.logger.debug("Registering core components")

        self._component_manager.register("config", ConfigComponent)
        self._component_manager.register("variables", VariableComponent)
        self._component_manager.register("patterns", PatternComponent)
        self._component_manager.register("units", FixedUnitComponent)
        self._component_manager.register("anchors", AnchorComponent)

        self.logger.debug("Components registered")

    def get_component(self, name: str) -> SystemComponent:
        """Get a component by name, loading it if necessary"""
        return self._component_manager.get(name)

    @property
    def config(self) -> ConfigComponent:
        return self.get_component("config")

    @property
    def utms_dir(self) -> str:
        """Get UTMS configuration directory"""
        return str(self._utms_dir)

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
