from typing import Dict, Any, List
from ..resolvers import PatternResolver, HyNode
from ..utils import get_logger, hy_to_python
from ..utms_types.recurrence.pattern import RecurrencePattern

logger = get_logger("loaders.pattern_loader")

_resolver = PatternResolver()

def parse_pattern_definitions(nodes: List[HyNode]) -> Dict[str, dict]:
    """Parse AST nodes into pattern specifications."""
    patterns = {}
    logger.debug("Starting to parse pattern definitions")

    for node in nodes:
        if node.type != "def-pattern":
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

        patterns[pattern_label] = {
            "label": pattern_label,
            "kwargs": pattern_kwargs
        }
        logger.info(f"Added pattern {pattern_label}")

    return patterns

def process_patterns(nodes: List[HyNode], variables: Dict[str, Any] = None) -> Dict[str, RecurrencePattern]:
    """Process Hy pattern definitions into fully initialized patterns."""
    logger.debug("Starting process_patterns")
    parsed_patterns = parse_pattern_definitions(nodes)
    logger.debug("Parsed patterns: %s", list(parsed_patterns.keys()))
    patterns = initialize_patterns(parsed_patterns, variables)
    logger.debug("Initialized patterns: %s", list(patterns.keys()))
    return patterns



def initialize_patterns(
    definitions: Dict[str, Any],
    variables: Dict[str, Any] = None
) -> Dict[str, RecurrencePattern]:
    """Initialize RecurrencePattern objects from definitions."""
    patterns = {}
    for label, definition in definitions.items():
        kwargs = definition["kwargs"]
        
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


        patterns[label] = pattern

    return patterns
