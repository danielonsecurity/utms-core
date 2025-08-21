# tests/utms_types/recurrence/test_pattern.py

import pytest
from datetime import datetime, time
import pytz
from utms.core.time import DecimalTimeStamp, DecimalTimeLength
from utms.utms_types.recurrence.pattern import RecurrencePattern
from utms.core.config import UTMSConfig # <-- Add this import

# Define a common timezone for all tests for consistency.
# Use a real timezone to test DST handling correctly.
PACIFIC_TZ = pytz.timezone('US/Pacific')

@pytest.fixture
def pattern_builder():
    """
    A pytest fixture that provides a factory for creating RecurrencePattern
    instances, correctly initialized with the REAL UnitManager's internal item dictionary.
    """
    config = UTMSConfig()
    # The TimeExpressionParser wants to call .items() on its provider.
    # The UnitManager's internal `_items` attribute is the dictionary that satisfies this.
    unit_items_dict = config.get_component("units")._unit_manager._items
    
    def factory(interval_str: str):
        # We now pass the correct object (the dictionary) to the constructor.
        return RecurrencePattern.every(interval_str, units_provider=unit_items_dict)
    
    return factory

def test_top_of_the_hour_pattern(pattern_builder):
    """USE CASE: (every "1h") (at [:minute 0])"""
    pattern = pattern_builder("1h").at_minute(0)
    last_run = PACIFIC_TZ.localize(datetime(2025, 8, 20, 9, 15, 0))
    
    next_occurrence = pattern.next_occurrence(DecimalTimeStamp(last_run), local_tz=PACIFIC_TZ)
    
    expected = PACIFIC_TZ.localize(datetime(2025, 8, 20, 10, 0, 0))
    assert next_occurrence.to_gregorian() == expected

def test_daily_lunch_break_pattern(pattern_builder):
    """USE CASE: (every "1d") (between "12:00" "13:00") (on weekdays)"""
    pattern = pattern_builder("1d") \
        .between("12:00", "13:00") \
        .on("monday", "tuesday", "wednesday", "thursday", "friday")

    # Start on a Friday afternoon, next occurrence should be Monday at noon.
    last_run = PACIFIC_TZ.localize(datetime(2025, 8, 22, 12, 30, 0)) # A Friday
    
    next_occurrence = pattern.next_occurrence(DecimalTimeStamp(last_run), local_tz=PACIFIC_TZ)
    
    expected = PACIFIC_TZ.localize(datetime(2025, 8, 25, 12, 0, 0)) # The following Monday
    assert next_occurrence.to_gregorian() == expected

def test_multiple_at_times_pattern(pattern_builder):
    """USE CASE: (every "1d") (at ["9:00" "16:30"])"""
    pattern = pattern_builder("1d").at("09:00", "16:30")

    # Start after the first time, should find the second time on the same day.
    last_run = PACIFIC_TZ.localize(datetime(2025, 8, 20, 9, 30, 0))
    
    next_occurrence = pattern.next_occurrence(DecimalTimeStamp(last_run), local_tz=PACIFIC_TZ)
    
    expected = PACIFIC_TZ.localize(datetime(2025, 8, 20, 16, 30, 0))
    assert next_occurrence.to_gregorian() == expected

def test_simple_interval_pattern(pattern_builder):
    """USE CASE: (every "2 minutes")"""
    pattern = pattern_builder("2 minutes")
    
    # Simple interval, no other constraints.
    last_run = PACIFIC_TZ.localize(datetime(2025, 8, 20, 10, 0, 0))
    
    next_occurrence = pattern.next_occurrence(DecimalTimeStamp(last_run), local_tz=PACIFIC_TZ)
    
    expected = PACIFIC_TZ.localize(datetime(2025, 8, 20, 10, 2, 0))
    assert next_occurrence.to_gregorian() == expected
    
def test_business_hours_with_exception_pattern(pattern_builder):
    """USE CASE: (every "30m") (between "9:00" "17:00") (except-between "12:00" "13:00")"""
    pattern = pattern_builder("30m") \
        .between("09:00", "17:00") \
        .except_between("12:00", "13:00")

    # Start just before the lunch break, next trigger should be at 13:00, skipping 12:00 and 12:30.
    last_run = PACIFIC_TZ.localize(datetime(2025, 8, 20, 11, 45, 0))
    
    next_occurrence = pattern.next_occurrence(DecimalTimeStamp(last_run), local_tz=PACIFIC_TZ)
    
    expected = PACIFIC_TZ.localize(datetime(2025, 8, 20, 13, 0, 0))
    assert next_occurrence.to_gregorian() == expected


def test_at_time_wraps_to_next_day(pattern_builder):
    """USE CASE: (at "09:00"), when the last run was after 9 AM."""
    pattern = pattern_builder("1d").at("09:00")
    last_run = PACIFIC_TZ.localize(datetime(2025, 10, 1, 10, 0, 0))
    next_occurrence = pattern.next_occurrence(DecimalTimeStamp(last_run), local_tz=PACIFIC_TZ)
    expected = PACIFIC_TZ.localize(datetime(2025, 10, 2, 9, 0, 0))
    assert next_occurrence.to_gregorian() == expected

def test_start_inside_exception_window(pattern_builder):
    """USE CASE: Starts inside the lunch break, should find the next valid time after."""
    pattern = pattern_builder("30m").between("09:00", "17:00").except_between("12:00", "13:00")
    last_run = PACIFIC_TZ.localize(datetime(2025, 8, 20, 12, 15, 0))
    next_occurrence = pattern.next_occurrence(DecimalTimeStamp(last_run), local_tz=PACIFIC_TZ)
    expected = PACIFIC_TZ.localize(datetime(2025, 8, 20, 13, 0, 0))
    assert next_occurrence.to_gregorian() == expected

def test_lunch_break_starting_on_weekend(pattern_builder):
    """USE CASE: Starts on a Saturday, must find the next valid weekday (Monday)."""
    pattern = pattern_builder("1d").between("12:00", "13:00").on("monday", "friday")
    last_run = PACIFIC_TZ.localize(datetime(2025, 8, 23, 10, 0, 0)) # A Saturday
    next_occurrence = pattern.next_occurrence(DecimalTimeStamp(last_run), local_tz=PACIFIC_TZ)
    expected = PACIFIC_TZ.localize(datetime(2025, 8, 25, 12, 0, 0)) # Following Monday
    assert next_occurrence.to_gregorian() == expected

def test_hourly_at_25_minutes(pattern_builder):
    """USE CASE: (every "1h") (at [:minute 25])"""
    pattern = pattern_builder("1h").at_minute(25)
    last_run = PACIFIC_TZ.localize(datetime(2025, 8, 20, 10, 30, 0)) # Start after the 10:25 mark
    next_occurrence = pattern.next_occurrence(DecimalTimeStamp(last_run), local_tz=PACIFIC_TZ)
    expected = PACIFIC_TZ.localize(datetime(2025, 8, 20, 11, 25, 0))
    assert next_occurrence.to_gregorian() == expected

def test_end_of_year_rollover(pattern_builder):
    """USE CASE: A daily task that correctly rolls over from Dec 31 to Jan 1."""
    pattern = pattern_builder("1d").at("08:00")
    last_run = PACIFIC_TZ.localize(datetime(2024, 12, 31, 8, 30, 0))
    next_occurrence = pattern.next_occurrence(DecimalTimeStamp(last_run), local_tz=PACIFIC_TZ)
    expected = PACIFIC_TZ.localize(datetime(2025, 1, 1, 8, 0, 0))
    assert next_occurrence.to_gregorian() == expected

def test_leap_day_handling(pattern_builder):
    """USE CASE: A daily task that correctly finds Feb 29 on a leap year."""
    pattern = pattern_builder("1d").at("10:00")
    last_run = PACIFIC_TZ.localize(datetime(2024, 2, 28, 11, 0, 0)) # 2024 is a leap year
    next_occurrence = pattern.next_occurrence(DecimalTimeStamp(last_run), local_tz=PACIFIC_TZ)
    expected = PACIFIC_TZ.localize(datetime(2024, 2, 29, 10, 0, 0))
    assert next_occurrence.to_gregorian() == expected

def test_weekend_backup_pattern(pattern_builder):
    """USE CASE: (every "12h") (at ["3:00", "15:00"]) (on weekend)"""
    pattern = pattern_builder("12h").at("03:00", "15:00").on("saturday", "sunday")
    last_run = PACIFIC_TZ.localize(datetime(2025, 8, 22, 16, 0, 0)) # A Friday afternoon
    next_occurrence = pattern.next_occurrence(DecimalTimeStamp(last_run), local_tz=PACIFIC_TZ)
    expected = PACIFIC_TZ.localize(datetime(2025, 8, 23, 3, 0, 0)) # Saturday at 3 AM
    assert next_occurrence.to_gregorian() == expected

def test_start_before_between_window(pattern_builder):
    """USE CASE: Starts before the 'between' window on a valid day."""
    pattern = pattern_builder("1h").between("14:00", "16:00")
    last_run = PACIFIC_TZ.localize(datetime(2025, 8, 20, 10, 0, 0))
    next_occurrence = pattern.next_occurrence(DecimalTimeStamp(last_run), local_tz=PACIFIC_TZ)
    expected = PACIFIC_TZ.localize(datetime(2025, 8, 20, 14, 0, 0))
    assert next_occurrence.to_gregorian() == expected

def test_start_after_between_window(pattern_builder):
    """USE CASE: Starts after the 'between' window, must find the next day."""
    pattern = pattern_builder("1h").between("14:00", "16:00")
    last_run = PACIFIC_TZ.localize(datetime(2025, 8, 20, 16, 30, 0))
    next_occurrence = pattern.next_occurrence(DecimalTimeStamp(last_run), local_tz=PACIFIC_TZ)
    expected = PACIFIC_TZ.localize(datetime(2025, 8, 21, 14, 0, 0))
    assert next_occurrence.to_gregorian() == expected

def test_very_specific_at_times(pattern_builder):
    """USE CASE: Multiple specific 'at' times, including one in the next morning."""
    pattern = pattern_builder("1d").at("14:17", "18:22", "04:30")
    last_run = PACIFIC_TZ.localize(datetime(2025, 8, 20, 15, 0, 0))
    next_occurrence = pattern.next_occurrence(DecimalTimeStamp(last_run), local_tz=PACIFIC_TZ)
    expected = PACIFIC_TZ.localize(datetime(2025, 8, 20, 18, 22, 0))
    assert next_occurrence.to_gregorian() == expected

def test_very_specific_at_times_wrapping_day(pattern_builder):
    """USE CASE: Same as above, but starts after the last time of the day."""
    pattern = pattern_builder("1d").at("14:17", "18:22", "04:30")
    last_run = PACIFIC_TZ.localize(datetime(2025, 8, 20, 19, 0, 0))
    next_occurrence = pattern.next_occurrence(DecimalTimeStamp(last_run), local_tz=PACIFIC_TZ)
    expected = PACIFIC_TZ.localize(datetime(2025, 8, 21, 4, 30, 0))
    assert next_occurrence.to_gregorian() == expected

def test_exact_start_time_match(pattern_builder):
    """USE CASE: If the last run is exactly a trigger time, find the *next* one."""
    pattern = pattern_builder("30m").between("09:00", "17:00")
    last_run = PACIFIC_TZ.localize(datetime(2025, 8, 20, 10, 0, 0))
    next_occurrence = pattern.next_occurrence(DecimalTimeStamp(last_run), local_tz=PACIFIC_TZ)
    expected = PACIFIC_TZ.localize(datetime(2025, 8, 20, 10, 30, 0))
    assert next_occurrence.to_gregorian() == expected

# --- Daylight Saving Time Edge Cases ---
# Note: DST dates are for 'US/Pacific'. Spring forward is the 2nd Sunday in March.
# Fall back is the 1st Sunday in November.

def test_dst_spring_forward(pattern_builder):
    """USE CASE: An hourly trigger that correctly jumps over the 'missing' hour during DST change."""
    pattern = pattern_builder("1h")
    # In 2025, DST starts on March 9. Clocks jump from 01:59:59 PST to 03:00:00 PDT.
    last_run = PACIFIC_TZ.localize(datetime(2025, 3, 9, 1, 30, 0)) # 1:30 AM PST
    next_occurrence = pattern.next_occurrence(DecimalTimeStamp(last_run), local_tz=PACIFIC_TZ)
    # The next trigger would be 2:30 AM, but that time does not exist.
    # The next *actual* time is 3:30 AM PDT.
    expected = PACIFIC_TZ.localize(datetime(2025, 3, 9, 3, 30, 0)) # 3:30 AM PDT
    assert next_occurrence.to_gregorian() == expected

def test_dst_fall_back(pattern_builder):
    """USE CASE: An hourly trigger during the 'repeated' hour of DST ending."""
    pattern = pattern_builder("1h")
    # In 2025, DST ends on Nov 2. Clocks jump from 01:59:59 PDT back to 01:00:00 PST.
    last_run = PACIFIC_TZ.localize(datetime(2025, 11, 2, 1, 30, 0), is_dst=True) # 1:30 AM PDT (the first time)
    next_occurrence = pattern.next_occurrence(DecimalTimeStamp(last_run), local_tz=PACIFIC_TZ)
    # The next trigger is one hour later, which is 1:30 AM PST (the second time).
    expected = PACIFIC_TZ.localize(datetime(2025, 11, 2, 1, 30, 0), is_dst=False) # 1:30 AM PST
    assert next_occurrence.to_gregorian() == expected

def test_complex_interval_expression(pattern_builder):
    """USE CASE: (every "2h + 15m")"""
    pattern = pattern_builder("2h + 15m")
    last_run = PACIFIC_TZ.localize(datetime(2025, 8, 20, 10, 0, 0))
    next_occurrence = pattern.next_occurrence(DecimalTimeStamp(last_run), local_tz=PACIFIC_TZ)
    expected = PACIFIC_TZ.localize(datetime(2025, 8, 20, 12, 15, 0))
    assert next_occurrence.to_gregorian() == expected

def test_complex_meeting_pattern_that_skips_lunch(pattern_builder):
    """USE CASE: A complex interval that must skip over the lunch exclusion."""
    pattern = pattern_builder("2h + 15m") \
        .between("09:00", "17:00") \
        .on("monday", "wednesday") \
        .except_between("12:00", "13:00")

    # Start at 11:00 on a Wednesday. The next trigger at 13:15 is inside the exclusion.
    # So the next valid trigger must be 15:30.
    last_run = PACIFIC_TZ.localize(datetime(2025, 8, 20, 11, 0, 0)) # Wednesday
    next_occurrence = pattern.next_occurrence(DecimalTimeStamp(last_run), local_tz=PACIFIC_TZ)
    expected = PACIFIC_TZ.localize(datetime(2025, 8, 20, 15, 30, 0))
    assert next_occurrence.to_gregorian() == expected

def test_at_minute_and_on_day(pattern_builder):
    """USE CASE: Fire at the top of every hour, but only on weekends."""
    pattern = pattern_builder("1h").at_minute(0).on("saturday", "sunday")
    last_run = PACIFIC_TZ.localize(datetime(2025, 8, 22, 12, 30, 0)) # Friday
    next_occurrence = pattern.next_occurrence(DecimalTimeStamp(last_run), local_tz=PACIFIC_TZ)
    expected = PACIFIC_TZ.localize(datetime(2025, 8, 23, 0, 0, 0)) # Midnight on Saturday
    assert next_occurrence.to_gregorian() == expected

def test_short_interval_across_day_boundary(pattern_builder):
    """USE CASE: A short interval that rolls over to the next day."""
    pattern = pattern_builder("30m")
    last_run = PACIFIC_TZ.localize(datetime(2025, 8, 20, 23, 45, 0))
    next_occurrence = pattern.next_occurrence(DecimalTimeStamp(last_run), local_tz=PACIFIC_TZ)
    expected = PACIFIC_TZ.localize(datetime(2025, 8, 21, 0, 15, 0))
    assert next_occurrence.to_gregorian() == expected

def test_pattern_with_no_future_occurrence_within_year(pattern_builder):
    """USE CASE: A pattern that cannot be satisfied should raise an error."""
    pattern = pattern_builder("1d").on("monday").between("09:00", "10:00")
    # Start time is after the window on the last possible Monday in the search range.
    last_run = PACIFIC_TZ.localize(datetime(2026, 8, 31, 11, 0, 0)) # A Monday
    with pytest.raises(RuntimeError):
        pattern.next_occurrence(DecimalTimeStamp(last_run), local_tz=PACIFIC_TZ)

def test_empty_constraints(pattern_builder):
    """USE CASE: A pattern with only an interval should behave predictably."""
    pattern = pattern_builder("1d")
    last_run = PACIFIC_TZ.localize(datetime(2025, 8, 20, 12, 34, 56))
    next_occurrence = pattern.next_occurrence(DecimalTimeStamp(last_run), local_tz=PACIFIC_TZ)
    expected = PACIFIC_TZ.localize(datetime(2025, 8, 21, 12, 34, 56))
    assert next_occurrence.to_gregorian() == expected    
