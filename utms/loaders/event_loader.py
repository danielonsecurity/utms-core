import os
from typing import Dict, Optional

from ..core.events import Event, EventConfig
from ..resolvers import EventResolver, evaluate_hy_file
from ..utils import get_logger, hy_to_python
from ..utms_types import ExpressionList, is_expression

logger = get_logger("core.events.event_loader")

_resolver = EventResolver()


def parse_event_definitions(event_data: ExpressionList) -> Dict[str, dict]:
    """Parse Hy event definitions into a dictionary of event specifications."""
    events = {}
    logger.debug("Starting to parse event definitions")

    for event_def_expr in event_data:
        if not is_expression(event_def_expr):
            continue

        if str(event_def_expr[0]) != "def-event":
            continue

        _, event_label_sym, *event_properties = event_def_expr
        event_label = str(event_label_sym)
        logger.debug("Processing event: %s", event_label)

        event_kwargs_dict = {}
        for prop_expr in event_properties:
            if is_expression(prop_expr):
                prop_name = str(prop_expr[0])
                prop_value = prop_expr[1]
                event_kwargs_dict[prop_name] = prop_value

        events[event_label] = {"label": event_label, "kwargs": event_kwargs_dict}
        logger.info("Added event %s", event_label)

    return events


def initialize_events(parsed_events, variables) -> dict:
    """Create Event instances from parsed definitions."""
    events = {}
    for event_label, event_info in parsed_events.items():
        kwargs = event_info["kwargs"]
        resolved_props = _resolver.resolve_event_property(kwargs, variables=variables)

        config = EventConfig(
            label=event_label,
            name=resolved_props.get("name"),
            state=resolved_props.get("state", ""),
            schedule=resolved_props.get("schedule"),
            deadline=resolved_props.get("deadline"),
            timestamp=resolved_props.get("timestamp"),
            timerange=resolved_props.get("timerange"),
            tags=resolved_props.get("tags", []),
            properties=resolved_props.get("properties", {}),
        )
        event = Event(config)
        events[event_label] = event

    return events
