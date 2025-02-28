from typing import Dict, List, Any
from ..loaders.base import ComponentLoader, LoaderContext
from ..managers.pattern import PatternManager
from utms.utms_types.recurrence.pattern import RecurrencePattern
from utms.core.hy.ast.node import HyNode
from utms.utils import get_logger, hy_to_python
from utms.core.hy.resolvers import PatternResolver

logger = get_logger("core.loaders.pattern")

class PatternLoader(ComponentLoader[RecurrencePattern, PatternManager]):
    """Loader for Pattern components."""

    def __init__(self, manager: PatternManager):
        super().__init__(manager)
        self._resolver = PatternResolver()

    def parse_definitions(self, nodes: List[HyNode]) -> Dict[str, dict]:
        """Parse HyNodes into pattern definitions."""
        patterns = {}
        logger.debug("Starting to parse pattern definitions")

        for node in nodes:
            if not self.validate_node(node, "def-pattern"):
                continue

            pattern_label = node.value
            logger.debug(f"Processing pattern: {pattern_label}")

            pattern_kwargs = {}
            for prop in node.children:
                if prop.type == "property":
                    prop_name = prop.value
                    if prop.children:
                        prop_value = prop.children[0].value
                        pattern_kwargs[prop_name] = prop_value
                        logger.debug(f"Added property {prop_name}: {prop_value}")

            patterns[pattern_label] = {"label": pattern_label, "kwargs": pattern_kwargs}
            logger.info(f"Added pattern {pattern_label}")

        return patterns

    def create_object(self, label: str, properties: Dict[str, Any]) -> RecurrencePattern:
        """Create a Pattern from properties."""
        kwargs = properties["kwargs"]

        # Create pattern with basic properties
        pattern = RecurrencePattern.every(hy_to_python(kwargs.get("every")))

        pattern.label = label
        pattern.name = hy_to_python(kwargs.get("name", label))

        # Apply additional properties
        if "at" in kwargs:
            times = hy_to_python(kwargs["at"])
            if not isinstance(times, list):
                times = [times]
            pattern.at(*times)

        if "between" in kwargs:
            between_times = hy_to_python(kwargs["between"])
            if isinstance(between_times, (list, tuple)) and len(between_times) == 2:
                pattern.between(between_times[0], between_times[1])

        if "on" in kwargs:
            days = hy_to_python(kwargs["on"])
            if not isinstance(days, list):
                days = [days]
            pattern.on(*days)

        if "except-between" in kwargs:
            except_times = hy_to_python(kwargs["except-between"])
            if isinstance(except_times, (list, tuple)) and len(except_times) == 2:
                pattern.except_between(except_times[0], except_times[1])

        if "groups" in kwargs:
            groups = hy_to_python(kwargs["groups"])
            if isinstance(groups, list):
                pattern.add_to_groups(*groups)
            else:
                pattern.add_to_groups(groups)

        return pattern

    def process(self, nodes: List[HyNode], context: LoaderContext) -> Dict[str, RecurrencePattern]:
        """Process nodes into Patterns with resolution context."""
        self.context = context
        return super().process(nodes, context)
