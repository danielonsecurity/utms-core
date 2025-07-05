import os
from typing import Dict, List, Optional

from utms.core.components.base import SystemComponent
from utms.core.hy.ast import HyAST
from utms.core.loaders.elements.pattern import PatternLoader
from utms.core.managers.elements.pattern import PatternManager
from utms.utms_types.recurrence.pattern import RecurrencePattern
from utms.core.loaders.base import LoaderContext

class PatternComponent(SystemComponent):
    """
    Component managing recurrence patterns.
    It now scans a dedicated 'patterns/' directory for all .hy definition files.
    """

    def __init__(self, config_dir: str, component_manager=None):
        super().__init__(config_dir, component_manager)
        self._patterns_dir = os.path.join(self._config_dir, "patterns")
        
        self._ast_manager = HyAST()
        self._pattern_manager = PatternManager()
        self._loader = PatternLoader(self._pattern_manager)

    def load(self) -> None:
        """
        Load patterns by scanning all .hy files in the 'patterns' directory.
        """
        if self._loaded:
            return
        self._items = {}
        self._loaded = True
        self.logger.debug(f"Component '{type(self).__name__}' is now live for loading.")

        os.makedirs(self._patterns_dir, exist_ok=True)
        
        all_loaded_patterns: Dict[str, RecurrencePattern] = {}

        try:
            # Get variables from variables component, same as EntityComponent.
            units_component = self.get_component("units")
            variables_component = self.get_component("variables")
            variables = (
                {name: var.value for name, var in variables_component.items()}
                if variables_component
                else {}
            )
            context = LoaderContext(config_dir=self._config_dir, variables=variables, dependencies={"units_provider": units_component})

            # Loop through all files in the patterns directory.
            for filename in os.listdir(self._patterns_dir):
                if filename.endswith(".hy"):
                    filepath = os.path.join(self._patterns_dir, filename)
                    self.logger.debug(f"Loading patterns from file: {filepath}")
                    try:
                        nodes = self._ast_manager.parse_file(filepath)
                        breakpoint()
                        patterns_from_file = self._loader.process(nodes, context)
                        self._items.update(patterns_from_file)
                        all_loaded_patterns.update(patterns_from_file)
                        self.logger.info(f"Loaded {len(patterns_from_file)} patterns from {filename}.")
                    except Exception as e_file:
                        self.logger.error(f"Error processing pattern file '{filepath}': {e_file}", exc_info=True)

            self.logger.info(f"PatternComponent loading complete. Total patterns loaded: {len(self._items)}")

        except Exception as e:
            self.logger.error(f"Fatal error during PatternComponent load: {e}", exc_info=True)
            self._loaded = False
            raise

    def save(self) -> None:
        """
        Save all in-memory patterns to a canonical 'default.hy' file
        inside the 'patterns' directory.
        """
        # For simplicity and robustness, we save all patterns to a single file.
        # This prevents issues with deleting patterns from files they weren't originally in.
        os.makedirs(self._patterns_dir, exist_ok=True)
        output_file = os.path.join(self._patterns_dir, "default.hy")
        
        nodes = [pattern.to_hy() for pattern in self._items.values()]
        
        try:
            with open(output_file, "w") as f:
                f.write(self._ast_manager.to_hy(nodes))
            self.logger.info(f"Saved {len(nodes)} patterns to '{output_file}'.")
        except Exception as e:
            self.logger.error(f"Failed to save patterns to '{output_file}': {e}", exc_info=True)


    # --- The rest of the public interface remains the same ---

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
