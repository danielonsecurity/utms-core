import math
from datetime import datetime
from unittest.mock import patch

import pytest

from utms.clock import *


def test_calculate_angles_noon():
    # Test with 12:00:00 (noon)
    seconds_since_midnight = 12 * 3600
    angles = calculate_angles(seconds_since_midnight, is_decimal=False)
    assert len(angles) == 5
    assert pytest.approx(angles[0]) == 0
    assert pytest.approx(angles[1]) == 0
    assert pytest.approx(angles[2]) == 0
    assert pytest.approx(angles[3]) == None
    assert pytest.approx(angles[4]) == None

    # Test decimal time
    angles_decimal = calculate_angles(seconds_since_midnight, is_decimal=True)
    assert len(angles_decimal) == 5
    assert pytest.approx(angles_decimal[0]) == math.pi
    assert pytest.approx(angles_decimal[1]) == 0
    assert pytest.approx(angles_decimal[2]) == 0
    assert pytest.approx(angles_decimal[3]) == 5
    assert pytest.approx(angles_decimal[4]) == 0


def test_calculate_angles_1500():
    # Test with 15:00:00 (noon)
    seconds_since_midnight = 15 * 3600
    angles = calculate_angles(seconds_since_midnight, is_decimal=False)
    assert len(angles) == 5
    assert pytest.approx(angles[0]) == math.pi / 2
    assert pytest.approx(angles[1]) == 0
    assert pytest.approx(angles[2]) == 0
    assert pytest.approx(angles[3]) == None
    assert pytest.approx(angles[4]) == None

    # Test decimal time
    angles_decimal = calculate_angles(seconds_since_midnight, is_decimal=True)
    assert len(angles_decimal) == 5
    assert pytest.approx(angles_decimal[0], abs=0.01) == 1.25 * math.pi
    assert pytest.approx(angles_decimal[1], abs=0.01) == 0.5 * math.pi
    assert pytest.approx(angles_decimal[2]) == math.pi
    assert pytest.approx(angles_decimal[3]) == 6
    assert pytest.approx(angles_decimal[4]) == 2


def test_calculate_angles_123456():
    # Test with 12:34:56
    seconds_since_midnight = 12 * 3600 + 34 * 60 + 56
    angles = calculate_angles(seconds_since_midnight, is_decimal=False)
    assert len(angles) == 5
    assert pytest.approx(angles[0], abs=0.01) == 0.1 * math.pi
    assert pytest.approx(angles[1], abs=0.01) == 1.165 * math.pi
    assert pytest.approx(angles[2], abs=0.01) == 1.866 * math.pi
    assert pytest.approx(angles[3]) == None
    assert pytest.approx(angles[4]) == None

    # Test decimal time
    angles_decimal = calculate_angles(seconds_since_midnight, is_decimal=True)
    assert len(angles_decimal) == 5
    assert pytest.approx(angles_decimal[0], abs=0.01) == 1.05 * math.pi
    assert pytest.approx(angles_decimal[1], abs=0.01) == 0.485 * math.pi
    assert pytest.approx(angles_decimal[2], abs=0.01) == 0.85 * math.pi
    assert pytest.approx(angles_decimal[3], abs=0.01) == 5
    assert pytest.approx(angles_decimal[4], abs=0.01) == 2


def test_prepare_hands_and_angles_analog():
    # Test prepare_hands_and_angles in analog mode
    hands = {"hour": 100, "minute": 150, "second": 200}
    angles = (0, math.pi / 2, math.pi)  # Example angles for hour, minute, and second
    is_decimal = False

    result = prepare_hands_and_angles(hands, angles, is_decimal)

    # Expected result for analog mode
    expected = [
        ("hour", 100, 0),
        ("minute", 150, math.pi / 2),
        ("second", 200, math.pi),
    ]

    assert result == expected


def test_prepare_hands_and_angles_decimal():
    # Test prepare_hands_and_angles in decimal mode
    hands = {"deciday": 120, "centiday": 80, "second": 200}
    angles = (math.pi, math.pi / 2, math.pi / 4, 5, 3)  # Example angles for decimal hands
    is_decimal = True

    result = prepare_hands_and_angles(hands, angles, is_decimal)

    # Expected result for decimal mode
    expected = [
        ("deciday", 120, math.pi),
        ("centiday", 80, math.pi / 2),
        ("second", 200, math.pi / 4),
    ]

    assert result == expected


def test_prepare_hands_and_angles_missing_hand():
    # Test with missing hand data in the `hands` dictionary
    hands = {"hour": 100, "minute": 150}  # 'second' hand is missing
    angles = (0, math.pi / 2, math.pi)
    is_decimal = False

    with pytest.raises(KeyError):
        prepare_hands_and_angles(hands, angles, is_decimal)


def test_prepare_hands_and_angles_extra_hands():
    # Test with extra hand data in the `hands` dictionary
    hands = {
        "hour": 100,
        "minute": 150,
        "second": 200,
        "extra": 50,  # Unused hand
    }
    angles = (0, math.pi / 2, math.pi)
    is_decimal = False

    result = prepare_hands_and_angles(hands, angles, is_decimal)

    # Expected result should not include 'extra'
    expected = [
        ("hour", 100, 0),
        ("minute", 150, math.pi / 2),
        ("second", 200, math.pi),
    ]

    assert result == expected


def test_prepare_hands_and_angles_no_hands():
    # Test with empty `hands` dictionary
    hands = {}
    angles = (0, math.pi / 2, math.pi)
    is_decimal = False

    with pytest.raises(KeyError):
        prepare_hands_and_angles(hands, angles, is_decimal)
