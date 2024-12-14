from datetime import datetime, timedelta, timezone

from utms.utils import resolve_date_dateparser, resolve_date

local_timezone = datetime.now().astimezone().tzinfo

def test_resolve_date():
    expected = datetime(2024, 12, 10, 0, 0, 0, tzinfo=local_timezone)
    actual = resolve_date("2024-12-10T00:00:00")
    assert actual == expected

def test_resolve_date_dateparser():
    expected = datetime(2024, 12, 10, 0, 0, 0, tzinfo=local_timezone)
    actual = resolve_date_dateparser("2024-12-10T00:00:00")
    assert actual == expected


def test_resolve_date_basic_format():
    expected = datetime(2024, 12, 10, 0, 0, 0, tzinfo=local_timezone)
    actual = resolve_date_dateparser("2024-12-10")
    assert actual == expected


def test_resolve_date_date_with_time():
    expected = datetime(2024, 12, 10, 14, 30, 0, tzinfo=local_timezone)
    actual = resolve_date_dateparser("2024-12-10 14:30")
    assert actual == expected


def test_resolve_date_with_am_pm():
    expected = datetime(2024, 12, 10, 9, 30, 0, tzinfo=local_timezone)  # 9:30 AM
    actual = resolve_date_dateparser("2024-12-10 9:30 AM")
    assert actual == expected


def test_resolve_date_with_timezone():
    expected = datetime(2024, 12, 10, 18, 45, 30, tzinfo=timezone(timedelta(hours=2)))
    actual = resolve_date_dateparser("2024-12-10 18:45:30+02:00")
    assert actual == expected


def test_resolve_date_named_month():
    expected = datetime(2024, 12, 10, 0, 0, 0, tzinfo=local_timezone)
    actual = resolve_date_dateparser("10 Dec 2024")
    assert actual == expected


def test_resolve_date_full_month_name():
    expected = datetime(2024, 12, 10, 0, 0, 0, tzinfo=local_timezone)
    actual = resolve_date_dateparser("10 December 2024")
    assert actual == expected


def test_resolve_date_with_day_of_week():
    expected = datetime(2024, 12, 10, 0, 0, 0, tzinfo=local_timezone)  # Tuesday
    actual = resolve_date_dateparser("Tue, 10 Dec 2024")
    assert actual == expected


def test_resolve_date_iso8601_format():
    expected = datetime(2024, 12, 10, 14, 30, 0, tzinfo=local_timezone)
    actual = resolve_date_dateparser("2024-12-10T14:30:00")
    assert actual == expected


def test_resolve_date_yesterday():
    expected = datetime.now().astimezone() - timedelta(days=1)
    actual = resolve_date_dateparser("yesterday")
    assert abs((actual - expected).total_seconds()) < 60


def test_resolve_date_relative_date():
    expected = datetime.now().astimezone() - timedelta(days=5)
    actual = resolve_date_dateparser("5 days ago")
    assert abs((actual - expected).total_seconds()) < 60


def test_resolve_wrong_date():
    actual = resolve_date_dateparser("blahblahblah")
    assert actual == None


