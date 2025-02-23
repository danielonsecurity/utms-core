import pytest
import calendar as py_calendar
import os
from utms.core.new_config import NewConfig
from utms.core.components.patterns import PatternComponent
from utms.utms_types.base.time import DecimalTimeStamp

def test_component_registration():
    config = NewConfig()
    
    # Test component registration
    assert not config._component_manager.is_loaded("patterns")
    
    # Test lazy loading
    patterns = config.patterns
    breakpoint()
    assert config._component_manager.is_loaded("patterns")
    assert isinstance(patterns, PatternComponent)

def test_pattern_loading(tmp_path):
    # Create a temporary patterns.hy file
    patterns_hy = """
(def-pattern DAILY-STANDUP
  (name "Daily Standup")
  (every "1d")
  (at "10:00")
  (on ["monday" "tuesday" "wednesday" "thursday" "friday"])
)

(def-pattern LUNCH-BREAK
  (name "Lunch Break")
  (every "1d")
  (between "12:00" "13:00")
  (on ["monday" "tuesday" "wednesday" "thursday" "friday"])
)
"""
    config_dir = tmp_path / "utms"
    config_dir.mkdir()
    patterns_file = config_dir / "patterns.hy"
    patterns_file.write_text(patterns_hy)

    # Initialize config with test directory
    config = NewConfig()
    config._utms_dir = str(config_dir)  # Override config directory
    
    # Get patterns component
    patterns = config.patterns
    
    # Test pattern loading
    assert "DAILY-STANDUP" in patterns.get_all_patterns()
    assert "LUNCH-BREAK" in patterns.get_all_patterns()

def test_pattern_functionality(tmp_path):
    # Similar setup as above
    patterns_hy = """
(def-pattern COMPLEX-MEETING
  (name "Complex Team Meeting")
  (every "2h + 15m")
  (between "9:00" "17:00")
  (on ["monday" "wednesday"])
  (except-between "12:00" "13:00")
)
"""
    config_dir = tmp_path / "utms"
    config_dir.mkdir()
    patterns_file = config_dir / "patterns.hy"
    patterns_file.write_text(patterns_hy)

    config = NewConfig()
    config._utms_dir = str(config_dir)
    
    # Get pattern
    pattern = config.patterns.get_pattern("COMPLEX-MEETING")
    assert pattern is not None
    
    # Test pattern behavior
    start_time = DecimalTimeStamp(1740167869)  # 2025-02-21 20:57:49
    next_time = pattern.next_occurrence(start_time)
    
    # Add assertions for expected next occurrence
    assert next_time > start_time
    # Add more specific assertions based on pattern rules

def test_pattern_saving(tmp_path):
    config_dir = tmp_path / "utms"
    config_dir.mkdir()
    
    config = NewConfig()
    config._utms_dir = str(config_dir)
    
    # Create and add a pattern
    from utms.utms_types.recurrence.pattern import RecurrencePattern
    pattern = RecurrencePattern.every("1d").at("10:00")
    pattern.name = "TEST-PATTERN"
    
    config.patterns.add_pattern(pattern)

    # Save patterns
    config.patterns.save()
    
    # Verify file was created
    patterns_file = config_dir / "patterns.hy"
    assert patterns_file.exists()
    
    # Load in new config and verify pattern exists
    new_config = NewConfig()
    new_config._utms_dir = str(config_dir)
    loaded_pattern = new_config.patterns.get_pattern("TEST-PATTERN")
    assert loaded_pattern is not None

def test_error_handling():
    config = NewConfig()
    
    # Test getting non-existent component
    with pytest.raises(KeyError):
        config.get_component("nonexistent")
    
    # Test getting non-existent pattern
    assert config.patterns.get_pattern("NONEXISTENT") is None
