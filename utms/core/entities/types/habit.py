from typing import Dict, ClassVar, List, Optional, Union
from enum import Enum
from decimal import Decimal
from utms.utms_types.entity.types import AttributeDefinition
from utms.utms_types.entity.attributes import CORE_ATTRIBUTES, EXTENDED_ATTRIBUTES
from utms.utms_types.base.time import DecimalTimeStamp, DecimalTimeLength
from ..base import TimeEntity
from utms.core.config import Config

config = Config()

class HabitType(str, Enum):
    """Type of habit - whether we want to increase or decrease it"""
    POSITIVE = "positive"  # Habits we want to build
    NEGATIVE = "negative"  # Habits we want to reduce
    NEUTRAL = "neutral"   # Habits we just want to track

class MeasurementType(str, Enum):
    """How the habit is measured"""
    BOOLEAN = "boolean"   # Did it happen or not
    COUNT = "count"       # How many times
    DURATION = "duration" # How long
    QUALITY = "quality"   # Rating/score

class HabitOccurrence:
    """Record of a single habit occurrence"""
    def __init__(
        self,
        timestamp: DecimalTimeStamp,
        value: Union[bool, int, float, Decimal],
        notes: str = ""
    ):
        self.timestamp = timestamp
        self.value = value
        self.notes = notes

class Habit(TimeEntity):
    """A habit entity with tracking capabilities"""
    
    attributes: ClassVar[Dict[str, AttributeDefinition]] = {
        **CORE_ATTRIBUTES,
        'habit_type': AttributeDefinition(str, default=HabitType.POSITIVE),
        'measurement': AttributeDefinition(str, default=MeasurementType.BOOLEAN),
        'target_value': AttributeDefinition(Decimal, default=Decimal('1')),
        'occurrences': AttributeDefinition(List[HabitOccurrence], default_factory=list),
        'current_streak': AttributeDefinition(int, default=0),
        'best_streak': AttributeDefinition(int, default=0),
        'description': EXTENDED_ATTRIBUTES['description'],
    }

    def __init__(
        self,
        name: str,
        habit_type: HabitType = HabitType.POSITIVE,
        measurement: MeasurementType = MeasurementType.BOOLEAN,
        target_value: Union[int, float, Decimal] = 1
    ):
        super().__init__(name)
        self.habit_type = habit_type
        self.measurement = measurement
        self.target_value = Decimal(str(target_value))
        self.occurrences = []
        self.current_streak = 0
        self.best_streak = 0

    def record(
        self,
        value: Union[bool, int, float, Decimal],
        timestamp: Optional[DecimalTimeStamp] = None,
        notes: str = ""
    ) -> None:
        """Record a habit occurrence"""
        if timestamp is None:
            timestamp = DecimalTimeStamp.now()

        occurrence = HabitOccurrence(timestamp, Decimal(str(value)), notes)
        self.occurrences.append(occurrence)
        self._update_streak()

    def get_today_total(self) -> Decimal:
        """Get total value for today"""
        today = DecimalTimeStamp.now()
        today_occurrences = [
            o for o in self.occurrences
            if o.timestamp.is_same_day(today)
        ]
        
        if not today_occurrences:
            return Decimal('0')
        
        return sum(o.value for o in today_occurrences)

    def get_streak(self) -> int:
        """Get current streak"""
        return self.current_streak

    def get_best_streak(self) -> int:
        """Get best streak"""
        return self.best_streak

    def get_progress(self) -> Decimal:
        """Get progress towards target as percentage"""
        today_total = self.get_today_total()
        if self.habit_type == HabitType.NEGATIVE:
            # For negative habits, less is better
            if today_total >= self.target_value:
                return Decimal('0')
            return ((self.target_value - today_total) / self.target_value) * 100
        else:
            # For positive habits, more is better
            if today_total >= self.target_value:
                return Decimal('100')
            return (today_total / self.target_value) * 100

    def time_since_last(self) -> Optional[DecimalTimeLength]:
        """Get time since last occurrence"""
        if not self.occurrences:
            return None
        
        last_occurrence = max(self.occurrences, key=lambda o: o.timestamp)
        diff = DecimalTimeStamp.now() - last_occurrence.timestamp
        return DecimalTimeLength(diff)

    def get_completion_rate(self, days: int = 30) -> Decimal:
        """Get completion rate over last n days"""
        if not self.occurrences:
            return Decimal('0')
        
        today = DecimalTimeStamp.now()
        completed_days = set()
        day_unit = config.units.get_unit("d")
        seconds_in_day = day_unit.value
        
        for occurrence in self.occurrences:
            time_diff = today - occurrence.timestamp
            days_passed = time_diff / seconds_in_day
            if days_passed <= days:
                completed_days.add(occurrence.timestamp.date())
        
        return Decimal(len(completed_days)) / Decimal(days) * 100

    def get_daily_average(self, days: int = 30) -> Decimal:
        """Get daily average over last n days"""
        if not self.occurrences:
            return Decimal('0')
        
        today = DecimalTimeStamp.now()
        day_unit = config.units.get_unit("d")
        seconds_in_day = day_unit.value
        recent_occurrences = [
            o for o in self.occurrences
            if (today - o.timestamp) / seconds_in_day <= days
        ]
        
        if not recent_occurrences:
            return Decimal('0')
        
        total = sum(o.value for o in recent_occurrences)
        return total / Decimal(days)

    def _update_streak(self) -> None:
        """Update streak counts"""
        # This is a simplified streak calculation
        # Could be made more sophisticated based on requirements
        today = DecimalTimeStamp.now()
        today_total = self.get_today_total()
        
        if self.habit_type == HabitType.NEGATIVE:
            if today_total <= self.target_value:
                self.current_streak += 1
            else:
                self.current_streak = 0
        else:
            if today_total >= self.target_value:
                self.current_streak += 1
            else:
                self.current_streak = 0
        
        if self.current_streak > self.best_streak:
            self.best_streak = self.current_streak
