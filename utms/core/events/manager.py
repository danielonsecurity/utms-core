from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

from .event import Event


class EventManager:
    def __init__(self):
        self.events: Dict[str, Event] = {}

    def add_event(self, event: Event):
        event_id = self._generate_id(event.name)
        self.events[event_id] = event

    def get_upcoming_events(
        self,
        from_time: Decimal,
        to_time: Optional[Decimal] = None,
        tags: Optional[List[str]] = None,
    ) -> List[Event]:
        """Get upcoming events within time range, filtered by tags."""
        if to_time is None:
            to_time = from_time + Decimal(7 * 24 * 3600)  # Default to week ahead

        events = []
        for event in self.events.values():
            # Check if event falls within time range
            if self._is_event_in_timerange(event, from_time, to_time):
                # Filter by tags if specified
                if tags and not any(tag in event.tags for tag in tags):
                    continue
                events.append(event)

        return sorted(
            events, key=lambda e: (e.schedule or e.deadline or e.timestamp or Decimal("inf"))
        )

    def get_deadlines(
        self, within: Decimal, from_time: Decimal, tags: Optional[List[str]] = None
    ) -> List[Event]:
        """Get upcoming deadlines within specified period."""
        events = []
        to_time = from_time + within

        for event in self.events.values():
            if event.deadline and from_time <= event.deadline <= to_time:
                if tags and not any(tag in event.tags for tag in tags):
                    continue
                events.append(event)

        return sorted(events, key=lambda e: e.deadline or Decimal("inf"))

    def get_schedule(self, time: Decimal, tags: Optional[List[str]] = None) -> List[Event]:
        """Get schedule for specific time."""
        events = []

        for event in self.events.values():
            if self._is_event_active_at(event, time):
                if tags and not any(tag in event.tags for tag in tags):
                    continue
                events.append(event)

        return sorted(events, key=lambda e: (e.schedule or e.timestamp or Decimal("inf")))

    def _is_event_in_timerange(self, event: Event, start: Decimal, end: Decimal) -> bool:
        """Check if event falls within the specified time range."""
        if event.schedule and start <= event.schedule <= end:
            return True
        if event.deadline and start <= event.deadline <= end:
            return True
        if event.timestamp and start <= event.timestamp <= end:
            return True
        if event.timerange:
            event_start = event.timerange.get("start")
            event_end = event.timerange.get("end")
            if event_start and event_end:
                return not (end < event_start or start > event_end)
        return False

    def _is_event_active_at(self, event: Event, time: Decimal) -> bool:
        """Check if event is active at specific time."""
        if event.schedule and event.schedule == time:
            return True
        if event.timestamp and event.timestamp == time:
            return True
        if event.timerange:
            event_start = event.timerange.get("start")
            event_end = event.timerange.get("end")
            if event_start and event_end:
                return event_start <= time <= event_end
        return False

    def update_event_state(self, event_id: str, new_state: str):
        if event_id not in self.events:
            raise KeyError(f"Event {event_id} not found")

        event = self.events[event_id]
        event.state = new_state

        if new_state.upper() == "DONE":
            event.closed = datetime.now()

    def _generate_id(self, name: str) -> str:
        return name.lower().replace(" ", "_")
