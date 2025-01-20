from datetime import datetime, timezone
from typing import Optional

import dateparser
from colorama import Fore, Style


def resolve_date_dateparser(input_text: str) -> Optional[datetime]:
    """Parses a string representing a date and returns the corresponding UTC
    datetime object.

    This function uses the `dateparser` library to parse the input
    date string into a datetime object.  If the parsed date is
    timezone-naive, it will be assumed to be in UTC and made
    timezone-aware.  The result is then returned as a UTC
    timezone-aware datetime object.

    Args:
        input_text (str): The input string containing the date to
                          parse. The string should represent a date in
                          a format supported by the `dateparser`
                          library.

    Returns:
        Optional[datetime]: A timezone-aware datetime object in UTC if
                             the parsing is successful.  Returns
                             `None` if the parsing fails.

    Example:
        >>> resolve_date_dateparser("2024-12-11 14:30")
        datetime.datetime(2024, 12, 11, 14, 30, tzinfo=datetime.timezone.utc)

    Exceptions:
        - If the input string cannot be parsed into a valid date,
          `None` will be returned.
        - If the parsed date is timezone-naive, it is assumed to be in
          UTC and made timezone-aware.

    Notes:
        - This function depends on the `dateparser` library to parse
          the input string.
        - The function ensures the returned datetime is in UTC and
          timezone-aware, even if the input date is naive.
    """
    parsed_date = dateparser.parse(input_text, settings={"RETURN_AS_TIMEZONE_AWARE": True})

    if parsed_date:
        print(Fore.RED + Style.BRIGHT + "dateparser: " + str(parsed_date) + Style.RESET_ALL)
        utc_date = parsed_date.astimezone(timezone.utc)
        return utc_date

    return None
