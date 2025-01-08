from datetime import datetime
from decimal import Decimal

from utms import AI, Config

local_timezone = datetime.now().astimezone().tzinfo

ai = AI(Config())

def test_ai_generate_date():
    expected = "2024-12-10T00:00:00+00:00"
    actual = ai.generate_date("10 December 2024")
    assert actual == expected


def test_ai_generate_date_elections():
    expected = "2024-11-05T00:00:00+00:00"
    actual = ai.generate_date("2024 US elections")
    assert actual == expected


def test_ai_generate_date_ww2():
    expected = "1945-09-02T00:00:00+00:00"
    actual = ai.generate_date("end of ww2")
    assert actual == expected


def test_ai_generate_date_unix_epoch():
    expected = "1970-01-01T00:00:00+00:00"
    actual = ai.generate_date("unix epoch")
    assert actual == expected


def test_ai_generate_date_fall_of_roman_empire():
    expected = "0476-09-04T00:00:00+00:00"
    actual = ai.generate_date("fall of roman empire")
    assert actual == expected


def test_ai_generate_date_tiannanmen_square():
    expected = "1989-06-04T00:00:00+00:00"
    actual = ai.generate_date("tiannanmen square massacre")
    assert actual == expected


def test_ai_generate_date_summer_olympics():
    expected = "2028-07"
    actual = ai.generate_date("2028 summer olympics")
    assert actual.startswith(expected)


def test_ai_generate_unknown_date():
    expected = "UNKNOWN"
    actual = ai.generate_date("blahblahblahblah")
    assert actual == expected


def test_ai_generate_future_date():
    expected = Decimal("+1.0e100")
    actual = Decimal(ai.generate_date("heat death of the universe"))
    assert actual >= expected


def test_ai_generate_date_before_era():
    expected = "-0044-03-15"
    actual = ai.generate_date("assassination of julius caesar")
    assert actual == expected
