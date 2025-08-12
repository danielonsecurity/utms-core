from typing import Any, Dict, List, Optional

from utms.core.hy.resolvers import PatternResolver
from utms.core.loaders.base import ComponentLoader, LoaderContext
from utms.core.managers.elements.pattern import PatternManager
from utms.utils import hy_to_python
from utms.utms_types import HyNode
from utms.utms_types.recurrence.pattern import RecurrencePattern


class PatternLoader(ComponentLoader[RecurrencePattern, PatternManager]):
    """Loader for Pattern components."""

    def __init__(self, manager: PatternManager, component: Optional[Any] = None):
        super().__init__(manager)
        self.component = component
        self._resolver = PatternResolver()

    def parse_definitions(self, nodes: List[HyNode]) -> Dict[str, dict]:
        """Parse HyNodes into pattern definitions."""
        patterns = {}
        self.logger.debug("Starting to parse pattern definitions")

        for node in nodes:
            if not self.validate_node(node, "def-pattern"):
                continue

            pattern_label = node.value
            self.logger.debug(f"Processing pattern: {pattern_label}")

            pattern_kwargs = {}
            for prop in node.children:
                if prop.type == "property":
                    prop_name = prop.value
                    if prop.children:
                        # This logic correctly handles both single and multiple values.
                        all_values = [child.value for child in prop.children]

                        # If the list has only one item, unpack it. Otherwise, keep the list.
                        prop_value = all_values[0] if len(all_values) == 1 else all_values

                        pattern_kwargs[prop_name] = prop_value
                        self.logger.debug(f"Added property {prop_name}: {repr(prop_value)}")

            patterns[pattern_label] = {"label": pattern_label, "kwargs": pattern_kwargs}
            self.logger.info(f"Added pattern {pattern_label}")

        return patterns

    def create_object(self, label: str, properties: Dict[str, Any]) -> RecurrencePattern:
        kwargs = properties["kwargs"]
        units_provider = self.context.dependencies.get("units_provider") if self.context and self.context.dependencies else None
        
        # We must create the base pattern from the 'every' clause first
        interval_str = hy_to_python(kwargs.get("every"))
        if not interval_str:
            raise ValueError(f"Pattern '{label}' must have an 'every' clause.")
        
        pattern = RecurrencePattern.every(interval_str, units_provider=units_provider)
        pattern.parser.units_provider = units_provider # Ensure parser has units

        pattern.label = label
        pattern.name = hy_to_python(kwargs.get("name", label))

        if "at" in kwargs:
            at_args = hy_to_python(kwargs["at"])
            
            # Check for special :minute format
            if isinstance(at_args, list) and len(at_args) == 2 and str(at_args[0]) == "minute":
                pattern.at_minute(int(at_args[1]))
            # Handle a single time string
            elif isinstance(at_args, str):
                pattern.at(at_args)
            # Handle a list of time strings
            elif isinstance(at_args, list):
                pattern.at(*at_args)

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
