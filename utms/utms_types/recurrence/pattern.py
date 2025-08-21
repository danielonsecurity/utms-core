# utms/utms_types/recurrence/pattern.py

from datetime import datetime, time, timedelta, timezone
from typing import Any, List, Optional, Union
import pytz

from utms.core.config.constants import (
    SECONDS_IN_DAY,
    SECONDS_IN_HOUR,
    SECONDS_IN_MINUTE,
    SECONDS_IN_WEEK,
)
from utms.core.time import DecimalTimeLength, DecimalTimeStamp, TimeExpressionParser
from utms.utms_types import HyNode, UnitManagerProtocol
from utms.core.hy.converter import converter
from .base import (
    Constraint,
    ConstraintFunc,
    FrequencyType,
    RecurrenceSpec,
)


class RecurrencePattern:
    def __init__(self, units_provider: Optional[UnitManagerProtocol] = None):
        self.name = None
        self.label = None
        self.spec = RecurrenceSpec()
        self.constraints: List[Constraint] = []
        self.groups = []
        self.parser = TimeExpressionParser(units_provider=units_provider)
        self.frequency_type: Optional[FrequencyType] = None
        self._original_interval: Optional[str] = None

    @classmethod
    def every(cls, interval: Union[str, DecimalTimeLength], units_provider: Optional[UnitManagerProtocol] = None) -> "RecurrencePattern":
        pattern = cls(units_provider=units_provider)
        if isinstance(interval, str):
            pattern._original_interval = interval
            pattern.spec.interval = pattern.parser.evaluate(interval)
            
            interval_seconds = pattern.spec.interval._seconds

            if interval_seconds == SECONDS_IN_HOUR:
                pattern.frequency_type = FrequencyType.HOURLY
            elif interval_seconds == SECONDS_IN_DAY:
                pattern.frequency_type = FrequencyType.DAILY
            elif interval_seconds == SECONDS_IN_WEEK:
                pattern.frequency_type = FrequencyType.WEEKLY
            elif interval_seconds == SECONDS_IN_MINUTE:
                pattern.frequency_type = FrequencyType.MINUTELY
            else:
                pattern.frequency_type = FrequencyType.CUSTOM
        else:
            pattern.spec.interval = interval
            pattern.frequency_type = FrequencyType.CUSTOM
        return pattern

    def on(self, *days: str) -> "RecurrencePattern":
        day_mapping = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6,
        }
        weekdays = {day_mapping[day.lower()] for day in days}
        self.spec.weekdays = weekdays
        
        def weekday_constraint(dt: datetime) -> bool:
            return dt.weekday() in weekdays
        
        self.add_constraint(weekday_constraint, f"On days: {', '.join(days)}")
        return self

    def at(self, *times: str) -> "RecurrencePattern":
        if not hasattr(self.spec, 'times') or self.spec.times is None:
            self.spec.times = []

        for t in times:
            value_to_process = converter.model_to_py(t, raw=True)
            if isinstance(value_to_process, list):
                self.spec.times.extend(value_to_process)
            else:
                self.spec.times.append(str(value_to_process))

        self.spec.times = sorted(list(set(self.spec.times)))
        return self
    
    def at_minute(self, minute: int) -> "RecurrencePattern":
        if not hasattr(self.spec, 'at_args') or self.spec.at_args is None:
            self.spec.at_args = []
        self.spec.at_args.append(('minute', minute))
        return self

    def between(self, start: str, end: str) -> "RecurrencePattern":
        self.spec.start_time = start
        self.spec.end_time = end
        
        try:
            start_parts = list(map(int, start.split(':')))
            end_parts = list(map(int, end.split(':')))
            start_time_obj = time(start_parts[0], start_parts[1])
            end_time_obj = time(end_parts[0], end_parts[1])
        except (ValueError, IndexError):
            raise ValueError(f"Invalid time format in between clause: '{start}' or '{end}'")

        def range_constraint(dt: datetime) -> bool:
            if dt is None: return False
            current_time = dt.time().replace(second=0, microsecond=0)
            return start_time_obj <= current_time < end_time_obj
        
        self.add_constraint(range_constraint, f"Between {start} and {end}")
        return self


    def next_occurrence(self, from_time: DecimalTimeStamp, local_tz: pytz.BaseTzInfo = pytz.utc) -> DecimalTimeStamp:
        gregorian_time = from_time.to_gregorian()
        if gregorian_time is None:
            raise ValueError(f"Cannot convert from_time '{from_time}' to a valid datetime object.")

        start_dt_local = gregorian_time.astimezone(local_tz)

        # Extract at rules and times once
        at_rules = dict(self.spec.at_args) if hasattr(self.spec, 'at_args') and self.spec.at_args else {}
        at_times = []
        if hasattr(self.spec, 'times') and self.spec.times:
            for t_str in self.spec.times:
                try: at_times.append(time.fromisoformat(str(t_str)))
                except ValueError: continue

        # Get interval in seconds as a float
        interval_seconds = float(self.spec.interval._seconds) if self.spec.interval else None

        # Fast path for simple interval patterns with no constraints
        if not self.constraints and not at_times and not at_rules and interval_seconds:
            # Just add the interval
            next_dt = start_dt_local + timedelta(seconds=interval_seconds)
            return DecimalTimeStamp(next_dt)

        # For patterns with specific times or constraints, use smarter jumping
        candidate_dt = start_dt_local

        # Safety limit - but now we'll jump more efficiently
        max_days = 365
        end_search = start_dt_local + timedelta(days=max_days)

        # Track when we started for interval calculations
        search_start = start_dt_local

        while candidate_dt < end_search:
            # Jump to next minute initially
            candidate_dt = candidate_dt.replace(second=0, microsecond=0) + timedelta(minutes=1)

            # Smart jumping based on constraints
            if at_times and not interval_seconds:
                # Jump to the next valid time on the same day or next day
                current_time = candidate_dt.time().replace(second=0, microsecond=0)
                next_time = None

                # Find next time today
                for t in sorted(at_times):
                    if t > current_time:
                        next_time = t
                        break

                if next_time:
                    # Jump to that time today
                    candidate_dt = candidate_dt.replace(hour=next_time.hour, minute=next_time.minute, second=0, microsecond=0)
                else:
                    # No more times today, jump to first time tomorrow
                    candidate_dt = (candidate_dt + timedelta(days=1)).replace(
                        hour=min(at_times).hour, 
                        minute=min(at_times).minute, 
                        second=0, 
                        microsecond=0
                    )

            # Check constraints
            if not all(constraint.func(candidate_dt) for constraint in self.constraints):
                continue

            # Check if this is a trigger time
            is_trigger_time = False

            if at_times:
                candidate_time_simple = candidate_dt.time().replace(second=0, microsecond=0)
                if candidate_time_simple in at_times:
                    is_trigger_time = True
            elif at_rules:
                if all(getattr(candidate_dt, key) == value for key, value in at_rules.items()):
                    is_trigger_time = True
            elif interval_seconds:
                # For interval patterns with constraints
                # We need to check if we've passed the interval since last run
                time_since_last = (candidate_dt - search_start).total_seconds()
                if time_since_last >= interval_seconds:
                    is_trigger_time = True
            else:
                # No specific timing rules, any valid time is a trigger
                is_trigger_time = True

            if is_trigger_time:
                # Ensure proper timezone
                if candidate_dt.tzinfo is None:
                    candidate_dt = local_tz.localize(candidate_dt)
                elif candidate_dt.tzinfo != local_tz:
                    candidate_dt = candidate_dt.astimezone(local_tz)
                return DecimalTimeStamp(candidate_dt)

        raise RuntimeError(f"Could not find a matching next occurrence for pattern '{self.label}' from {start_dt_local}")

    def except_between(self, start: str, end: str) -> "RecurrencePattern":
        try:
            start_parts = list(map(int, start.split(':')))
            end_parts = list(map(int, end.split(':')))
            except_start = time(start_parts[0], start_parts[1])
            except_end = time(end_parts[0], end_parts[1])
        except (ValueError, IndexError):
            raise ValueError(f"Invalid time format in except_between clause: '{start}' or '{end}'")
        
        def exclude_range_constraint(dt: datetime) -> bool:
            if dt is None: return True
            return not (except_start <= dt.time().replace(second=0, microsecond=0) < except_end)
        
        self.add_constraint(exclude_range_constraint, f"Except between {start} and {end}")
        return self

    def add_constraint(self, func: ConstraintFunc, description: str) -> None:
        self.constraints.append(Constraint(func, description))

    def to_hy(self) -> HyNode:
        def make_property(name: str, value: Any, original: str = None) -> HyNode:
            return HyNode(
                type="property", value=name,
                children=[HyNode(type="value", value=value, original=original, is_dynamic=bool(original))]
            )
        properties = []
        if self.name: properties.append(make_property("name", self.name))
        if self._original_interval: properties.append(make_property("every", self._original_interval))
        elif self.spec.interval: properties.append(make_property("every", str(self.spec.interval)))
        
        if hasattr(self.spec, 'at_args') and self.spec.at_args:
            for arg in self.spec.at_args:
                if isinstance(arg, tuple) and len(arg) == 2 and arg[0] == 'minute':
                    properties.append(make_property("at", [f":{arg[0]}", arg[1]]))
        elif hasattr(self.spec, 'times') and self.spec.times:
             properties.append(make_property("at", self.spec.times))

        if self.spec.start_time and self.spec.end_time: properties.append(make_property("between", [self.spec.start_time, self.spec.end_time]))
        if self.spec.weekdays:
            weekday_names = {0: "monday", 1: "tuesday", 2: "wednesday", 3: "thursday", 4: "friday", 5: "saturday", 6: "sunday"}
            days = [weekday_names[day] for day in sorted(self.spec.weekdays)]
            properties.append(make_property("on", days))
        if hasattr(self.spec, 'except_times') and self.spec.except_times:
            for start, end in self.spec.except_times:
                properties.append(make_property("except-between", [start, end]))
        if hasattr(self, "groups") and self.groups: properties.append(make_property("groups", self.groups))

        return HyNode(type="def-pattern", value=self.label, children=properties)

    def add_to_groups(self, *groups: str) -> "RecurrencePattern":
        if not hasattr(self, "groups"): self.groups = []
        self.groups.extend(groups)
        return self
