from typing import List, Union
from utms.utms_types.base.time import DecimalTimeStamp
from .base import BuilderProtocol, RecurrencePatternProtocol

class TimeBuilder:
    def __init__(self, pattern: RecurrencePatternProtocol):
        self.pattern = pattern

    def at(self, *times: str) -> RecurrencePatternProtocol:
        """Set specific times"""
        self.pattern.spec.times = set(times)
        
        def time_constraint(ts: DecimalTimeStamp) -> bool:
            current_time = ts.time().strftime("%H:%M")
            return current_time in self.pattern.spec.times
        
        self.pattern.add_constraint(
            time_constraint,
            f"At times: {', '.join(times)}"
        )
        return self.pattern

    def between(self, start: str, end: str) -> RecurrencePatternProtocol:
        """Set time range"""
        self.pattern.spec.start_time = start
        self.pattern.spec.end_time = end
        
        def range_constraint(ts: DecimalTimeStamp) -> bool:
            current_time = ts.time().strftime("%H:%M")
            return start <= current_time < end
        
        self.pattern.add_constraint(
            range_constraint,
            f"Between {start} and {end}"
        )
        return self.pattern

class RecurrenceBuilder:
    def __init__(self, pattern: RecurrencePatternProtocol):
        self.pattern = pattern

    def on(self, *days: str) -> TimeBuilder:
        """Set specific days"""
        day_mapping = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2,
            'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        weekdays = {day_mapping[day.lower()] for day in days}
        self.pattern.spec.weekdays = weekdays
        
        def weekday_constraint(ts: DecimalTimeStamp) -> bool:
            return ts.weekday() in weekdays
        
        self.pattern.add_constraint(
            weekday_constraint,
            f"On days: {', '.join(days)}"
        )
        return TimeBuilder(self.pattern)

    def at(self, *times: str) -> RecurrencePatternProtocol:
        return TimeBuilder(self.pattern).at(*times)

    def between(self, start: str, end: str) -> RecurrencePatternProtocol:
        return TimeBuilder(self.pattern).between(start, end)
