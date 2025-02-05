from .registry import FormatRegistry
from .calendar import CalendarFormatter

# Create and configure the global registry
registry = FormatRegistry()
registry.register("CALENDAR", CalendarFormatter())
