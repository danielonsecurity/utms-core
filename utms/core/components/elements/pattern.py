import os
from typing import Dict, List, Optional

from utms.core.components.base import SystemComponent
from utms.core.hy.ast import HyAST
from utms.core.loaders.elements.pattern import PatternLoader
from utms.core.managers.elements.pattern import PatternManager
from utms.utms_types.recurrence.pattern import RecurrencePattern
from utms.core.loaders.base import LoaderContext
from utms.utms_types.field.types import TypedValue

class PatternComponent(SystemComponent):
    """
    Component managing recurrence patterns.
    It scans a global 'patterns/' directory and a user-specific 'patterns/' directory.
    """

    def __init__(self, config_dir: str, component_manager=None, username: Optional[str] = None):
        super().__init__(config_dir, component_manager)
        self._ast_manager = HyAST()
        self._pattern_manager = PatternManager()
        self._loader = PatternLoader(self._pattern_manager)

        self._global_patterns_dir = os.path.join(self._config_dir, "global", "patterns")
        self._user_patterns_dir = None
        effective_user = username
        if not effective_user:
            self.logger.warning("PatternComponent initialized without a username; falling back to 'active-user' from global config.")
            config_component = self.get_component("config")
            if not config_component.is_loaded(): config_component.load()
            active_user_config = config_component.get_config("active-user")
            effective_user = active_user_config.get_value() if active_user_config else None

        if effective_user:
            self.logger.info(f"PatternComponent is operating for user: '{effective_user}'")
            user_root = os.path.join(self._config_dir, "users", effective_user)
            self._user_patterns_dir = os.path.join(user_root, "patterns")
        else:
            self.logger.warning("No active or specified user; only global patterns will be loaded.")

    def load(self) -> None:
        """Load patterns from global and user directories."""
        if self._loaded:
            return
        
        def _process_dir(path, context):
            if not (path and os.path.isdir(path)):
                return
            os.makedirs(path, exist_ok=True)
            for filename in os.listdir(path):
                if not filename.endswith(".hy"): continue
                filepath = os.path.join(path, filename)
                try:
                    nodes = self._ast_manager.parse_file(filepath)
                    self._items.update(self._loader.process(nodes, context))
                except Exception as e_file:
                    self.logger.error(f"Error processing pattern file '{filepath}': {e_file}")

        self._pattern_manager.clear()
        self._items = self._pattern_manager.get_all()

        variables_component = self.get_component("variables")
        variables = {}
        if variables_component:
            for name, var_model in variables_component.items():
                if hasattr(var_model, 'value') and isinstance(var_model.value, TypedValue):
                    py_value = var_model.value.value
                    variables[name] = py_value
                    if '-' in name:
                        variables[name.replace('-', '_')] = py_value
        units_component = self.get_component("units")
        context = LoaderContext(
            config_dir=self._config_dir, 
            variables=variables, 
            dependencies={"units_provider": units_component}
        )

        _process_dir(self._global_patterns_dir, context) 
        _process_dir(self._user_patterns_dir, context)   

        self._loaded = True

    def save(self) -> None:
        """
        Save all in-memory patterns to a canonical 'default.hy' file
        inside the 'patterns' directory.
        """
        if not self._user_patterns_dir:
            self.logger.error("Cannot save patterns: No active/specified user directory is configured.")
            return

        os.makedirs(self._user_patterns_dir, exist_ok=True)
        output_file = os.path.join(self._user_patterns_dir, "default.hy")
        nodes = [pattern.to_hy() for pattern in self._items.values()]
        
        try:
            with open(output_file, "w") as f:
                f.write(self._ast_manager.to_hy(nodes))
            self.logger.info(f"Saved {len(nodes)} patterns to '{output_file}'.")
        except Exception as e:
            self.logger.error(f"Failed to save patterns to '{output_file}': {e}", exc_info=True)


    def get_pattern(self, name: str) -> Optional[RecurrencePattern]:
        """Get a pattern by name"""
        return self.get(name)

    def add_pattern(self, pattern: RecurrencePattern) -> None:
        """Add a pattern"""
        if not pattern.label:
            pattern.label = pattern.name
        self[pattern.label] = pattern

    def get_all_patterns(self) -> Dict[str, RecurrencePattern]:
        """Get all patterns"""
        return dict(self)

    def get_patterns_by_group(self, group: str) -> List[RecurrencePattern]:
        """Get all patterns belonging to a specific group"""
        return self._pattern_manager.get_patterns_by_group(group)

    def create_pattern(
        self,
        label: str,
        name: str,
        every: str,
        at: Optional[List[str]] = None,
        between: Optional[tuple[str, str]] = None,
        on: Optional[List[str]] = None,
        except_between: Optional[tuple[str, str]] = None,
        groups: Optional[List[str]] = None,
    ) -> RecurrencePattern:
        """Create a new pattern with the given properties"""
        pattern = self._pattern_manager.create(
            label=label, name=name, every=every, at=at,
            between=between, on=on, except_between=except_between, groups=groups,
        )
        self._items[label] = pattern
        return pattern

    def remove_pattern(self, label: str) -> None:
        """Remove a pattern by label"""
        if label in self._items:
            del self._items[label]
            self._pattern_manager.remove(label)

    @property
    def patterns(self) -> Dict[str, RecurrencePattern]:
        """Access all patterns (alias for backward compatibility)"""
        return self.get_all_patterns()
