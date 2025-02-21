from typing import Optional, List, Union
from datetime import datetime, time, timedelta  # Add time to imports
from utms.utms_types.base.time import DecimalTimeStamp, DecimalTimeLength
from utms.utms_types.base.time_parser import TimeExpressionParser
from .base import (
    RecurrenceSpec,
    Modifier,
    Constraint,
    FrequencyType,
    ModifierFunc,
    ConstraintFunc,
    RecurrencePatternProtocol
)
from .builders import RecurrenceBuilder

class RecurrencePattern:
    def __init__(self):
        self.spec = RecurrenceSpec()
        self.modifiers: List[Modifier] = []
        self.constraints: List[Constraint] = []
        self.parser = TimeExpressionParser()

    @classmethod
    def every(cls, interval: Union[str, DecimalTimeLength]) -> 'RecurrencePattern':
        pattern = cls()
        if isinstance(interval, str):
            pattern.spec.interval = pattern.parser.evaluate(interval)
        else:
            pattern.spec.interval = interval
        return pattern

    def on(self, *days: str) -> 'RecurrencePattern':
        day_mapping = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2,
            'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6
        }
        weekdays = {day_mapping[day.lower()] for day in days}
        
        def weekday_constraint(ts: DecimalTimeStamp) -> bool:
            dt = ts.to_gregorian()
            if dt is None:
                return False
            return dt.weekday() in weekdays
        
        self.add_constraint(weekday_constraint, f"On days: {', '.join(days)}")
        return self

    def at(self, *times: str) -> 'RecurrencePattern':
        """Set specific times"""
        # Store times in spec
        self.spec.times = set(times)

        time_objs = []
        for time_str in times:
            try:
                hour, minute = map(int, time_str.split(':'))
                time_objs.append(time(hour, minute))
            except ValueError:
                raise ValueError(f"Invalid time format: {time_str}. Use HH:MM format.")

        def time_constraint(ts: DecimalTimeStamp) -> bool:
            dt = ts.to_gregorian()
            if dt is None:
                return False
            current_time = dt.time().replace(second=0, microsecond=0)
            return any(current_time == t for t in time_objs)

        self.add_constraint(time_constraint, f"At times: {', '.join(times)}")
        return self



    def between(self, start: str, end: str) -> 'RecurrencePattern':
        """Set time range"""
        self.spec.start_time = start
        self.spec.end_time = end

        # Parse time strings
        start_hour, start_minute = map(int, start.split(':'))
        end_hour, end_minute = map(int, end.split(':'))
        start_time = time(start_hour, start_minute)
        end_time = time(end_hour, end_minute)

        def range_constraint(ts: DecimalTimeStamp) -> bool:
            dt = ts.to_gregorian()
            if dt is None:
                return False
            current_time = dt.time().replace(second=0, microsecond=0)
            return start_time <= current_time < end_time

        self.add_constraint(range_constraint, f"Between {start} and {end}")
        return self

    def next_occurrence(self, from_time: DecimalTimeStamp) -> DecimalTimeStamp:
        candidate = from_time + self.spec.interval
        max_iterations = 1000
        iterations = 0

        while iterations < max_iterations:
            iterations += 1
            dt = candidate.to_gregorian()
            if dt:
                current_time = dt.time()

                # Handle specific times
                if self.spec.times:
                    target_times = sorted([
                        time(hour, minute) 
                        for time_str in self.spec.times
                        for hour, minute in [map(int, time_str.split(':'))]
                    ])

                    # Try today's target times
                    next_time = None
                    for target in target_times:
                        candidate_time = DecimalTimeStamp(
                            dt.replace(hour=target.hour, 
                                     minute=target.minute, 
                                     second=0).timestamp()
                        )
                        if candidate_time > from_time:
                            next_time = target
                            break

                    if next_time:
                        candidate = DecimalTimeStamp(
                            dt.replace(hour=next_time.hour, 
                                     minute=next_time.minute, 
                                     second=0).timestamp()
                        )
                    else:
                        # Go to first time tomorrow
                        tomorrow = dt.replace(hour=0, minute=0, second=0) + timedelta(days=1)
                        candidate = DecimalTimeStamp(
                            tomorrow.replace(hour=target_times[0].hour,
                                          minute=target_times[0].minute,
                                          second=0).timestamp()
                        )

                # Handle time range
                elif hasattr(self.spec, 'start_time') and self.spec.start_time is not None:
                    start_hour, start_minute = map(int, self.spec.start_time.split(':'))
                    end_hour, end_minute = map(int, self.spec.end_time.split(':'))
                    start_time = time(start_hour, start_minute)
                    end_time = time(end_hour, end_minute)

                    if current_time < start_time:
                        # Align to interval within range
                        base = dt.replace(hour=start_hour, minute=start_minute, second=0)
                        candidate = DecimalTimeStamp(base.timestamp())
                    elif current_time >= end_time:
                        # Go to start time tomorrow
                        tomorrow = dt.replace(hour=0, minute=0, second=0) + timedelta(days=1)
                        candidate = DecimalTimeStamp(
                            tomorrow.replace(hour=start_hour,
                                          minute=start_minute,
                                          second=0).timestamp()
                        )
                    else:
                        # We're within the range, align to interval
                        seconds_since_midnight = current_time.hour * 3600 + current_time.minute * 60
                        interval_seconds = float(self.spec.interval._seconds)
                        next_interval = ((seconds_since_midnight // interval_seconds) + 1) * interval_seconds

                        # Create timestamp for next interval
                        base = dt.replace(hour=0, minute=0, second=0)
                        candidate = DecimalTimeStamp(base.timestamp() + next_interval)

                # Check all constraints
                if all(constraint.func(candidate) for constraint in self.constraints):
                    return candidate

            # If constraints not met or no special handling needed
            candidate += self.spec.interval

        raise RuntimeError(f"Could not find next occurrence after {max_iterations} iterations")



    def except_between(self, start: str, end: str) -> 'RecurrencePattern':
        """Exclude a time range"""
        # Parse time strings
        start_hour, start_minute = map(int, start.split(':'))
        end_hour, end_minute = map(int, end.split(':'))
        except_start = time(start_hour, start_minute)
        except_end = time(end_hour, end_minute)

        def exclude_range_constraint(ts: DecimalTimeStamp) -> bool:
            dt = ts.to_gregorian()
            if dt is None:
                return True  # If we can't convert to gregorian, don't exclude
            current_time = dt.time().replace(second=0, microsecond=0)
            # Return True if time is OUTSIDE the excluded range
            return not (except_start <= current_time < except_end)

        self.add_constraint(
            exclude_range_constraint,
            f"Except between {start} and {end}"
        )
        return self


    def add_modifier(self, func: ModifierFunc, description: str) -> None:
        self.modifiers.append(Modifier(func, description))

    def add_constraint(self, func: ConstraintFunc, description: str) -> None:
        self.constraints.append(Constraint(func, description))
