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
    
    # Test 1: Basic interval recurrence
    pattern = RecurrencePattern.every("2h")
    start_time = DecimalTimeStamp(1740167869)
    
    print("\nTest 1: Every 2 hours")
    next_time = pattern.next_occurrence(start_time)
    print(f"Start time: {start_time}")
    print(f"Next occurrence: {next_time.to_gregorian()}")
    print(f"Difference: {next_time - start_time} seconds")
    assert next_time - start_time == 7200, "Should be 2 hours later"

    # Test 2: Weekday recurrence
    pattern = RecurrencePattern.every("1d").on("monday", "wednesday", "friday")
    
    print("\nTest 2: Every MWF")
    next_time = pattern.next_occurrence(start_time)
    print(f"Start time: {start_time}")
    print(f"Next occurrence: {next_time.to_gregorian()}")
    dt = next_time.to_gregorian()
    print(f"Day of week: {dt.weekday()}")  # Should be 0, 2, or 4
    assert dt.weekday() in {0, 2, 4}, "Should be Monday, Wednesday, or Friday"


    # Test 3: Specific times
    print("\nTest 3: Daily at 10:00")
    pattern = RecurrencePattern.every("1d").at("10:00")
    print(f"Start time: {start_time.to_gregorian()}")
    next_time = pattern.next_occurrence(start_time)
    print(f"Next occurrence: {next_time.to_gregorian()}")
    dt = next_time.to_gregorian()
    print(f"Time: {dt.time()}")
    assert dt.time().hour == 10 and dt.time().minute == 0

    # Test 4: Combined patterns
    pattern = (RecurrencePattern.every("1d")
              .on("monday", "wednesday", "friday")
              .at("10:00", "15:00"))
    
    print("\nTest 4: MWF at 10:00 and 15:00")
    next_time = pattern.next_occurrence(start_time)
    print(f"Start time: {start_time}")
    print(f"Next occurrence: {next_time.to_gregorian()}")
    dt = next_time.to_gregorian()
    print(f"Day: {dt.weekday()}, Time: {dt.time()}")
    assert dt.weekday() in {0, 2, 4}
    assert dt.time().hour in {10, 15}

    # Test 5: Between times
    pattern = (RecurrencePattern.every("2h")
              .between("9:00", "17:00"))
    
    print("\nTest 5: Every 2 hours between 9:00 and 17:00")
    next_time = pattern.next_occurrence(start_time)
    print(f"Start time: {start_time}")
    print(f"Next occurrence: {next_time.to_gregorian()}")
    dt = next_time.to_gregorian()
    print(f"Time: {dt.time()}")
    assert 9 <= dt.time().hour < 17

    # Test 6: Complex pattern
    pattern = (RecurrencePattern.every("1d")
              .on("monday", "wednesday", "friday")
              .between("9:00", "17:00")
              .except_between("12:00", "13:00"))  # Lunch hour
    
    print("\nTest 6: MWF business hours except lunch")
    next_time = pattern.next_occurrence(start_time)
    print(f"Start time: {start_time}")
    print(f"Next occurrence: {next_time.to_gregorian()}")
    dt = next_time.to_gregorian()
    print(f"Day: {dt.weekday()}, Time: {dt.time()}")
    assert dt.weekday() in {0, 2, 4}
    assert 9 <= dt.time().hour < 17
    assert dt.time().hour != 12

    # Test 7: Multiple occurrences
    pattern = RecurrencePattern.every("4h")
    
    print("\nTest 7: Next 5 occurrences every 4 hours")
    current = start_time
    for i in range(5):
        current = pattern.next_occurrence(current)
        print(f"Occurrence {i+1}: {current}")
        if i > 0:
            assert current - prev_time == 14400  # 4 hours
        prev_time = current


if __name__ == "__main__":
    test_event()
    test_task()
    test_habit()
    parser = TimeExpressionParser()
    for expr in test_cases:
        print(parser.evaluate(expr))
    test_recurrence_patterns()
    
