from datetime import datetime

from uts.ai import ai_generate_date

local_timezone = datetime.now().astimezone().tzinfo


def test_ai_generate_date():
    # Expected datetime with timezone info (UTC)
    expected = "2024-12-10T00:00:00+00:00"

    # Call your resolve_date function
    actual = ai_generate_date("10 December 2024")
    assert actual == expected


def test_ai_generate_date_elections():
    # Expected datetime with timezone info (UTC)
    expected = "2024-11-05T00:00:00+00:00"

    # Call your resolve_date function
    actual = ai_generate_date("2024 US elections")
    assert actual == expected
    

def test_ai_generate_date_ww2():
    # Expected datetime with timezone info (UTC)
    expected = "1945-09-02T00:00:00+00:00"

    # Call your resolve_date function
    actual = ai_generate_date("end of ww2")
    assert actual == expected
    
def test_ai_generate_date_unix_epoch():
    # Expected datetime with timezone info (UTC)
    expected = "1970-01-01T00:00:00+00:00"

    # Call your resolve_date function
    actual = ai_generate_date("unix epoch")
    assert actual == expected
    
def test_ai_generate_date_fall_of_roman_empire():
    # Expected datetime with timezone info (UTC)
    expected = "0476-09-04T00:00:00+00:00"

    # Call your resolve_date function
    actual = ai_generate_date("fall of roman empire")
    assert actual == expected
    
    
def test_ai_generate_date_tiananmen_square():
    # Expected datetime with timezone info (UTC)
    expected = "1989-06-04T00:00:00+00:00"

    # Call your resolve_date function
    actual = ai_generate_date("tiananmen square massacre")
    assert actual == expected
    
def test_ai_generate_date_summer_olympics():
    # Expected datetime with timezone info (UTC)
    expected = "2028-07-26T00:00:00+00:00"

    # Call your resolve_date function
    actual = ai_generate_date("2028 summer olympics")
    assert actual == expected
    
