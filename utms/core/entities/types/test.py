from utms.utms_types.base.time import DecimalTimeStamp, DecimalTimeLength
from utms.utms_types.recurrence.pattern import RecurrencePattern
from utms.utms_types.base.time import DecimalTimeStamp, DecimalTimeRange
from utms.utms_types.entity.time_specs import TimeStampSpec, TimeRangeSpec
from utms.core.entities.types.event import Event
from utms.core.entities.types.task import Task
from utms.core.entities.types.habit import Habit, HabitType, MeasurementType
from utms.utms_types.base.time_parser import TimeExpressionParser


def test_event():
    # Create an event
    event = Event("Team Meeting")

    # Set some attributes
    event.scheduled = TimeStampSpec(
        timestamp=DecimalTimeStamp(1234567890)
    )

    event.ranges = [
        TimeRangeSpec(
            timerange=DecimalTimeRange(
                DecimalTimeStamp(1234567890),
                DecimalTimeStamp(1234571490)
            )
        )
    ]

    event.location = "Conference Room A"
    event.state = "TODO"
    event.tags = ["work", "team"]
    event.priority = "A"

    # Access attributes
    print(f"Event: {event.name}")
    print(f"Scheduled: {event.scheduled.timestamp}")
    print(f"Location: {event.location}")
    print(f"State: {event.state}")
    print(f"Tags: {event.tags}")


def test_task():
    # Create a task
    task = Task("Implement UTMS Task System")

    # Set some attributes
    task.scheduled = TimeStampSpec(
        timestamp=DecimalTimeStamp(1234567890)
    )
    task.deadline = TimeStampSpec(
        timestamp=DecimalTimeStamp(1234571490)
    )
    
    task.tags = ["development", "priority"]
    task.priority = "A"
    task.description = "Implement the task management system for UTMS"

    # Test state changes
    print("\n=== Task Test ===")
    print(f"Task: {task.name}")
    print(f"Initial State: {task.state}")
    print(f"Is Active: {task.is_active()}")
    
    task.mark_next()
    print(f"After mark_next: {task.state}")
    print(f"Is Active: {task.is_active()}")
    
    task.mark_done()
    print(f"After mark_done: {task.state}")
    print(f"Is Done: {task.is_done()}")
    print(f"Is Active: {task.is_active()}")
    
    print(f"\nOther Attributes:")
    print(f"Scheduled: {task.scheduled.timestamp}")
    print(f"Deadline: {task.deadline.timestamp}")
    print(f"Tags: {task.tags}")
    print(f"Priority: {task.priority}")
    print(f"Description: {task.description}")


def test_habit():
    # Create habits
    exercise = Habit(
        name="Daily Exercise",
        habit_type=HabitType.POSITIVE,
        measurement=MeasurementType.DURATION
    )
    
    water = Habit(
        name="Drink Water",
        habit_type=HabitType.POSITIVE,
        measurement=MeasurementType.COUNT,
        target_value=8  # glasses per day
    )
    
    smoking = Habit(
        name="Smoking",
        habit_type=HabitType.NEGATIVE,
        measurement=MeasurementType.COUNT,
        target_value=0
    )

    print("\n=== Habit Test ===")
    
    # Record and show exercise
    exercise.record(value=30)  # 30 minutes
    print("Exercise Habit:")
    print(f"Name: {exercise.name}")
    print(f"Type: {exercise.habit_type}")
    print(f"Today's value: {exercise.get_today_total()} minutes")
    print(f"Target: {exercise.target_value} minutes")
    print(f"Progress: {exercise.get_progress()}%")
    
    # Record and show water intake
    water.record(value=1)  # one glass
    water.record(value=1)  # another glass
    print("\nWater Intake:")
    print(f"Today's count: {water.get_today_total()} glasses")
    print(f"Target: {water.target_value} glasses")
    print(f"Progress: {water.get_progress()}%")
    
    # Record and show smoking
    smoking.record(value=1)
    time_since = smoking.time_since_last()
    print("\nSmoking Tracking:")
    print(f"Today's count: {smoking.get_today_total()}")
    if time_since:
        minutes = time_since._seconds / 60  # Convert to minutes
        print(f"Time since last: {minutes:.1f} minutes")
    print(f"Target: {smoking.target_value}")
    print(f"Progress: {smoking.get_progress()}%")
    
    # Show analytics for all habits
    print("\nHabit Analytics:")
    for habit in [exercise, water, smoking]:
        print(f"\n{habit.name}:")
        print(f"Completion rate: {habit.get_completion_rate():.1f}%")
        print(f"Best streak: {habit.get_best_streak()} days")
        print(f"Average per day: {habit.get_daily_average():.1f}")

test_cases = [
    "2h + (30m / 2)",     # 8100
    "(1h + 30m) * 2",     # 10800 seconds (5400 * 2)
    "24h / 6 + 15m",      # 15300 seconds (14400 + 900)
    "1.5e-1h",          # 540 seconds (0.15 hours)
    "(2h + 15m) * 1.5 + 45m",  # 14850
    "3h - 15m + 2 * 30s"       # 9960
]

def test_recurrence_patterns():
    print("\n=== Testing Recurrence Patterns ===")
    
    # Basic intervals
    tests = [
        ("2h", "Every 2 hours"),
        ("1d", "Every day"),
        ("30m", "Every 30 minutes"),
        ("2h + 15m", "Every 2 hours and 15 minutes"),
        ("1d + 12h", "Every day and a half"),
        ("3h + 45m + 30s", "Complex interval"),
    ]
    
    start_time = DecimalTimeStamp(1740167869)  # 2025-02-21 20:57:49
    for interval, description in tests:
        print(f"\nTest: {description}")
        pattern = RecurrencePattern.every(interval)
        next_time = pattern.next_occurrence(start_time)
        print(f"Start: {start_time.to_gregorian()}")
        print(f"Next: {next_time.to_gregorian()}")
        print(f"Difference: {next_time - start_time} seconds")

    # Day patterns
    day_patterns = [
        (["monday", "wednesday", "friday"], "MWF"),
        (["monday"], "Mondays only"),
        (["saturday", "sunday"], "Weekends"),
        (["monday", "tuesday", "wednesday", "thursday", "friday"], "Weekdays"),
    ]

    for days, description in day_patterns:
        print(f"\nTest: {description}")
        pattern = RecurrencePattern.every("1d").on(*days)
        next_time = pattern.next_occurrence(start_time)
        print(f"Start: {start_time.to_gregorian()}")
        print(f"Next: {next_time.to_gregorian()}")

    # Time patterns
    time_patterns = [
        (["9:00"], "Daily at 9:00"),
        (["9:00", "13:00", "17:00"], "Three times daily"),
        (["0:00"], "Midnight"),
        (["23:59"], "End of day"),
    ]

    for times, description in time_patterns:
        print(f"\nTest: {description}")
        pattern = RecurrencePattern.every("1d").at(*times)
        next_time = pattern.next_occurrence(start_time)
        print(f"Start: {start_time.to_gregorian()}")
        print(f"Next: {next_time.to_gregorian()}")

    # Time ranges
    range_patterns = [
        ("9:00", "17:00", "2h", "Business hours every 2h"),
        ("0:00", "6:00", "1h", "Night shift hourly"),
        ("6:00", "22:00", "4h", "Extended hours every 4h"),
    ]

    for start, end, interval, description in range_patterns:
        print(f"\nTest: {description}")
        pattern = RecurrencePattern.every(interval).between(start, end)
        next_time = pattern.next_occurrence(start_time)
        print(f"Start: {start_time.to_gregorian()}")
        print(f"Next: {next_time.to_gregorian()}")

    # Complex patterns
    print("\nTest: Business days at specific times")
    pattern = (RecurrencePattern.every("1d")
              .on("monday", "tuesday", "wednesday", "thursday", "friday")
              .at("9:00", "13:00", "17:00"))
    next_time = pattern.next_occurrence(start_time)
    print(f"Start: {start_time.to_gregorian()}")
    print(f"Next: {next_time.to_gregorian()}")

    print("\nTest: Weekend mornings")
    pattern = (RecurrencePattern.every("1d")
              .on("saturday", "sunday")
              .between("6:00", "12:00"))
    next_time = pattern.next_occurrence(start_time)
    print(f"Start: {start_time.to_gregorian()}")
    print(f"Next: {next_time.to_gregorian()}")

    print("\nTest: Complex interval with specific times")
    pattern = (RecurrencePattern.every("2h + 15m + 30s")
              .between("9:00", "17:00"))
    next_time = pattern.next_occurrence(start_time)
    print(f"Start: {start_time.to_gregorian()}")
    print(f"Next: {next_time.to_gregorian()}")

    print("\nTest: Business hours with lunch break")
    pattern = (RecurrencePattern.every("1h")
              .between("9:00", "17:00")
              .except_between("12:00", "13:00"))
    next_time = pattern.next_occurrence(start_time)
    print(f"Start: {start_time.to_gregorian()}")
    print(f"Next: {next_time.to_gregorian()}")

    # Multiple occurrences
    print("\nTest: Next 5 occurrences of complex pattern")
    pattern = RecurrencePattern.every("2h + 30m").between("9:00", "17:00")
    current = start_time
    for i in range(5):
        current = pattern.next_occurrence(current)
        print(f"Occurrence {i+1}: {current.to_gregorian()}")


if __name__ == "__main__":
    test_event()
    test_task()
    test_habit()
    parser = TimeExpressionParser()
    for expr in test_cases:
        print(parser.evaluate(expr))
    test_recurrence_patterns()
    
