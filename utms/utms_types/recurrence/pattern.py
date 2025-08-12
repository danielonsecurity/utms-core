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
from utms.utils import hy_to_python
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
            value_to_process = hy_to_python(t)
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

        at_times = []
        if hasattr(self.spec, 'times') and self.spec.times:
            parsed_times = []
            for t_str in self.spec.times:
                try:
                    parts = list(map(int, str(t_str).split(':')))
                    hour, minute = parts[0], parts[1]
                    second = parts[2] if len(parts) > 2 else 0
                    parsed_times.append(time(hour, minute, second))
                except (ValueError, IndexError):
                    continue
            at_times = sorted(parsed_times)

        # --- Logic for patterns WITHOUT 'at' clauses ---
        if not at_times:
            candidate_dt_local = start_dt_local

            # For sub-day intervals (like '30m' or '2h 15m')
            if self.spec.interval.to_timedelta() < timedelta(days=1):
                for _ in range(10000): # Safety break
                    candidate_dt_local += self.spec.interval.to_timedelta()
                    if all(constraint.func(candidate_dt_local) for constraint in self.constraints):
                        return DecimalTimeStamp(candidate_dt_local)
                raise RuntimeError(f"Could not find next valid sub-day interval for '{self.label}'")

            # For day-or-longer intervals (like '1d' for LUNCH-BREAK)
            else:
                search_date = start_dt_local.date()
                # If the potential start of the window today is already in the past, start searching from tomorrow
                if self.spec.start_time:
                    start_time_obj = time.fromisoformat(self.spec.start_time)
                    today_candidate = local_tz.localize(datetime.combine(search_date, start_time_obj))
                    if today_candidate <= start_dt_local:
                        search_date += timedelta(days=1)

                for _ in range(366): # Search up to a year
                    # Construct the first possible candidate for this day (e.g., 12:00)
                    if self.spec.start_time:
                        start_time_obj = time.fromisoformat(self.spec.start_time)
                        candidate_dt = local_tz.localize(datetime.combine(search_date, start_time_obj))

                        # Check if this single candidate is valid
                        if candidate_dt > start_dt_local and all(constraint.func(candidate_dt) for constraint in self.constraints):
                            return DecimalTimeStamp(candidate_dt)

                    # If no valid start time or it failed, move to the next day
                    search_date += timedelta(days=1)

            raise RuntimeError(f"Could not find next valid interval for '{self.label}'")

        # --- Logic for patterns WITH 'at' times (This part works well) ---
        current_date_local = start_dt_local.date()
        if all(local_tz.localize(datetime.combine(current_date_local, t)) <= start_dt_local for t in at_times):
            current_date_local += timedelta(days=1)

        for _ in range(366):
            for t_local in at_times:
                naive_dt = datetime.combine(current_date_local, t_local)
                aware_dt_local = local_tz.localize(naive_dt, is_dst=None)

                if aware_dt_local > start_dt_local:
                    if all(constraint.func(aware_dt_local) for constraint in self.constraints):
                        return DecimalTimeStamp(aware_dt_local)

            current_date_local += timedelta(days=1)

        raise RuntimeError(f"Could not find next 'at' occurrence for '{self.label}' within a year.")

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
