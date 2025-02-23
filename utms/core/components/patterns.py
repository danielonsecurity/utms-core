import os
from typing import Dict, Optional
from utms.utils import get_logger
from .base import SystemComponent
from utms.resolvers import HyAST
from utms.utms_types.recurrence.pattern import RecurrencePattern
from utms.loaders.pattern_loader import process_patterns


class PatternComponent(SystemComponent):
    """Component managing recurrence patterns"""
    
    def __init__(self, config_dir: str):
        super().__init__(config_dir)
        self._ast_manager = HyAST()

    def load(self) -> None:
        """Load patterns from patterns.hy"""
        if self._loaded:
            return

        patterns_file = os.path.join(self._config_dir, "patterns.hy")
        if os.path.exists(patterns_file):
            try:
                nodes = self._ast_manager.parse_file(patterns_file)
                pattern_instances = process_patterns(nodes)
                self._items = pattern_instances
                self._loaded = True
            except Exception as e:
                self._logger.error(f"Error loading patterns: {e}")
                raise

    def save(self) -> None:
        """Save patterns to patterns.hy"""
        patterns_file = os.path.join(self._config_dir, "patterns.hy")
        nodes = [pattern.to_hy() for pattern in self._items.values()]
        with open(patterns_file, "w") as f:
            f.write(self._ast_manager.to_hy(nodes))

    def is_loaded(self) -> bool:
        """Check if patterns have been loaded"""
        return self._loaded

    # These methods now become simple aliases
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
