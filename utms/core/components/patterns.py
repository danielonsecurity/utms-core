import os
from typing import Dict, List, Optional

from utms.core.hy.ast import HyAST
from utms.utms_types.recurrence.pattern import RecurrencePattern

from utms.core.managers.pattern import PatternManager
from utms.core.loaders.pattern import PatternLoader
from .base import SystemComponent


class PatternComponent(SystemComponent):
    """Component managing recurrence patterns"""

    def __init__(self, config_dir: str, component_manager=None):
        super().__init__(config_dir, component_manager)
        self._ast_manager = HyAST()
        self._pattern_manager = PatternManager()
        self._loader = PatternLoader(self._pattern_manager)

    def load(self) -> None:
        """Load patterns from patterns.hy"""
        if self._loaded:
            return

        patterns_file = os.path.join(self._config_dir, "patterns.hy")
        if os.path.exists(patterns_file):
            try:
                # Get variables from variables component if needed
                variables_component = self.get_component("variables")
                variables = {
                    name: var.value for name, var in variables_component.items()
                } if variables_component else {}

                # Parse file into nodes
                nodes = self._ast_manager.parse_file(patterns_file)

                # Create context
                from ..loaders.base import LoaderContext
                context = LoaderContext(
                    config_dir=self._config_dir,
                    variables=variables
                )

                # Process nodes using loader
                self._items = self._loader.process(nodes, context)
                self._loaded = True

            except Exception as e:
                self.logger.error(f"Error loading patterns: {e}")
                raise

    def save(self) -> None:
        """Save patterns to patterns.hy"""
        patterns_file = os.path.join(self._config_dir, "patterns.hy")
        # Convert patterns to nodes using their to_hy method
        nodes = [pattern.to_hy() for pattern in self._items.values()]
        # Write using AST manager
        with open(patterns_file, "w") as f:
            f.write(self._ast_manager.to_hy(nodes))

    # Original interface methods
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

    # New functionality
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
            label=label,
            name=name,
            every=every,
            at=at,
            between=between,
            on=on,
            except_between=except_between,
            groups=groups,
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
