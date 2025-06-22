from typing import Dict, List, Optional

from utms.core.managers.base import BaseManager
from utms.utms_types.recurrence.pattern import RecurrencePattern


class PatternManager(BaseManager[RecurrencePattern]):
    """Manages RecurrencePattern objects."""

    def create(
        self, label: str, name: str = None, every: str = None, **kwargs
    ) -> RecurrencePattern:
        """Create a new pattern."""
        if label in self._items:
            raise ValueError(f"Pattern with label '{label}' already exists")

        # Let the RecurrencePattern handle its own creation
        pattern = RecurrencePattern.every(every) if every else RecurrencePattern()
        pattern.label = label
        pattern.name = name or label

        self.add(label, pattern)
        return pattern

    def get_patterns_by_group(self, group: str) -> List[RecurrencePattern]:
        """Get all patterns belonging to a specific group."""
        return [pattern for pattern in self._items.values() if group in pattern.groups]

    def get_patterns_by_groups(
        self, groups: List[str], match_all: bool = False
    ) -> List[RecurrencePattern]:
        """Get patterns belonging to multiple groups."""
        if match_all:
            return [
                pattern
                for pattern in self._items.values()
                if all(group in pattern.groups for group in groups)
            ]
        else:
            return [
                pattern
                for pattern in self._items.values()
                if any(group in pattern.groups for group in groups)
            ]

    def serialize(self) -> Dict[str, Dict]:
        """Convert patterns to serializable format."""
        return {
            pattern.label: {
                "name": pattern.name,
                "every": pattern.every,
                "at": pattern.at_times if hasattr(pattern, "at_times") else None,
                "between": (
                    (pattern.between_start, pattern.between_end)
                    if hasattr(pattern, "between_start")
                    else None
                ),
                "on": pattern.on_days if hasattr(pattern, "on_days") else None,
                "except_between": (
                    (pattern.except_start, pattern.except_end)
                    if hasattr(pattern, "except_start")
                    else None
                ),
                "groups": pattern.groups,
            }
            for pattern in self._items.values()
        }

    def deserialize(self, data: Dict[str, Dict]) -> None:
        """Load patterns from serialized data."""
        self.clear()
        for label, pattern_data in data.items():
            pattern = RecurrencePattern.every(pattern_data.get("every"))
            pattern.label = label
            pattern.name = pattern_data.get("name", label)

            if pattern_data.get("at"):
                pattern.at(*pattern_data["at"])

            if pattern_data.get("between"):
                pattern.between(*pattern_data["between"])

            if pattern_data.get("on"):
                pattern.on(*pattern_data["on"])

            if pattern_data.get("except_between"):
                pattern.except_between(*pattern_data["except_between"])

            if pattern_data.get("groups"):
                pattern.add_to_groups(*pattern_data["groups"])

            self.add(label, pattern)
