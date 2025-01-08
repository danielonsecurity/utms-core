from datetime import datetime, timezone
from decimal import Decimal
from typing import List

import pytest

from utms import constants
from utms.anchors import Anchor, AnchorConfig, AnchorManager
from utms.config import Config
from utms.units import UnitManager

config = Config()
units = config.units
anchors = AnchorManager(units)


@pytest.fixture
def anchor_config() -> AnchorConfig:
    """Fixture to provide a sample AnchorConfig."""
    return AnchorConfig(
        label="TA",
        name="Test Anchor",
        value=Decimal(1234567),
        breakdowns=[["h", "m", "s"]],
        groups=[],
        precision=Decimal(1e-6),
    )


@pytest.fixture
def anchor(anchor_config: AnchorConfig) -> Anchor:
    """Fixture to provide a sample Anchor."""
    return Anchor(anchor_config)


def test_anchor_initialization(anchor_config):
    """Test initialization of the Anchor class."""
    anchor = Anchor(anchor_config)
    assert anchor.name == "Test Anchor"
    assert anchor.value == Decimal(1234567)
    assert anchor.precision == Decimal(1e-6)
    assert anchor.breakdowns == [["h", "m", "s"]]


def test_anchor_from_datetime():
    """Test creating an Anchor from a datetime object."""
    test_datetime = datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc)
    anchor = Anchor(AnchorConfig("DA", "Date Anchor", test_datetime))

    assert anchor.name == "Date Anchor"
    assert isinstance(anchor.value, Decimal)
    assert anchor.value == Decimal(test_datetime.timestamp())
    assert anchor.breakdowns == [
        ["Y"],
        ["Ga", "Ma", "Mn", "Y", "d", "h", "m", "s"],
        ["PS", "TS", "GS", "MS", "KS", "s"],
    ]


def test_anchor_from_decimal():
    """Test creating an Anchor from a Decimal value."""
    test_value = Decimal(5000)
    anchor = Anchor(AnchorConfig("DA", "Decimal Anchor", test_value))

    assert anchor.name == "Decimal Anchor"
    assert anchor.value == test_value
    assert anchor.precision == Decimal(1e-6)
    assert anchor.breakdowns == [
        ["Y"],
        ["Ga", "Ma", "Mn", "Y", "d", "h", "m", "s"],
        ["PS", "TS", "GS", "MS", "KS", "s"],
    ]


def test_anchor_breakdown(anchor):
    """Test the breakdown method for an Anchor."""
    result = anchor.breakdown(Decimal(12345), units)
    assert result
    assert "h" in result
    assert "m" in result
    assert "s" in result


def test_anchor_manager_initialization():
    """Test initialization of the AnchorManager class."""
    anchors = AnchorManager(units)
    assert len(anchors) == 0


def test_anchor_manager_add_anchor():
    """Test adding an anchor to the AnchorManager."""
    length = len(anchors)
    anchors.add_anchor(AnchorConfig("test", "Test Anchor", Decimal(12345)))

    assert len(anchors) == length + 1
    assert "test" in anchors._anchors


def test_anchor_manager_add_anchor_datetime():
    """Test creating an Anchor from a datetime object."""
    length = len(anchors)
    test_datetime = datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc)

    anchors.add_anchor(AnchorConfig("datetime_test", "Datetime Anchor", test_datetime))

    assert len(anchors) == length + 1
    assert "test" in anchors._anchors


def test_anchor_manager_add_anchor_datetime2():
    """Test creating an Anchor from a datetime object."""
    length = len(anchors)
    test_datetime = datetime(1912, 2, 1, 12, 0, tzinfo=timezone.utc)

    anchors.add_anchor(AnchorConfig("old_datetime_test", "Old datetime Anchor", test_datetime))

    assert len(anchors) == length + 1
    assert "old_datetime_test" in anchors._anchors


def test_anchor_manager_get_item():
    """Test accessing an anchor by label or index."""
    anchors.add_anchor(AnchorConfig("new", "New Anchor", Decimal(12345)))

    assert anchors["new"].name == "New Anchor"
    assert anchors[len(anchors) - 1].name == "New Anchor"

    with pytest.raises(KeyError):
        anchors["invalid"]

    with pytest.raises(IndexError):
        anchors[10]


def test_anchor_manager_iter():
    """Test iteration over the anchors in the manager."""

    length = len(anchors)
    anchors.add_anchor(AnchorConfig("a1", "Anchor 1", Decimal(1000)))
    anchors.add_anchor(AnchorConfig("a2", "Anchor 2", Decimal(2000)))

    for i in anchors:
        assert i in anchors
    assert len(anchors) == length + 2
    assert anchors[length].name == "Anchor 1"
    assert anchors[length + 1].name == "Anchor 2"


def test_anchor_manager_get_label():
    """Test retrieving a label by an Anchor instance."""
    anchors.add_anchor(AnchorConfig("test", "Test Anchor", Decimal(12345)))
    anchor = anchors["test"]

    label = anchors.get_label(anchor)
    assert label == "test"

    with pytest.raises(ValueError):
        anchors.get_label(Anchor(AnchorConfig("test", "Invalid", Decimal(0),
                                              precision=Decimal(1e-6),
                                              breakdowns=[["s"]])))


def test_from_datetime_pre_epoch():
    # Test a datetime before January 2, 0001
    pre_epoch_date = datetime(1, 1, 1, 23, 59, tzinfo=timezone.utc)
    anchor = Anchor(AnchorConfig("PE", "Pre-Epoch Test", pre_epoch_date))

    expected_value = Decimal(pre_epoch_date.timestamp()) - Decimal(constants.SECONDS_IN_YEAR)

    assert anchor.value == expected_value
    assert anchor.name == "Pre-Epoch Test"


def test_calculate_breakdown_continue():
    anchor = Anchor(AnchorConfig("test", "Test Anchor", Decimal(3600)))
    breakdown_units = ["invalid", "h", "m"]

    # Call the method
    result = anchor._calculate_breakdown(Decimal(3600), breakdown_units, units)

    # Assert the breakdown skips the "invalid" unit and proceeds
    assert "h" in result[0]  # Valid unit processed
    assert all("invalid" not in entry for entry in result)  # Invalid skipped


def test_calculate_zero_breakdown():
    anchor = Anchor(AnchorConfig("test", "Test Anchor", Decimal(0)))
    breakdown_units = ["h", "m", "s"]

    # Call the method
    result = anchor._calculate_breakdown(Decimal(0), breakdown_units, units)

    assert result == ["0 \x1b[34ms\x1b[0m             "]


def test_breakdown_continue():
    # Mock UnitManager
    anchor = Anchor(AnchorConfig("test", "Test Anchor", Decimal(3600), precision=Decimal(0.01)))
    anchor.breakdowns = [["h", "s"], ["valid"]]

    # Call the method
    result = anchor.breakdown(Decimal(3600), units)

    # Assert breakdown skips invalid/too_small units and continues
    assert "valid" not in result  # "invalid" and "too_small" were skipped
