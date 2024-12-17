"""
Module for Time Calculations, Conversion, and Formatting

This module provides various functions related to time calculations, including resolving
dates, calculating Universal Planck Count (UPC), converting time into different units,
and formatting the output for display. The module uses NTP (Network Time Protocol) to
fetch accurate timestamps and offers utilities for handling time in both human-readable
formats and scientific units such as petaseconds, teraseconds, and gigaseconds.

Key Features:
- Fetching NTP time and converting to UTC datetime.
- Calculating total time since the Big Bang and Universal Planck Count.
- Converting time to different units and displaying it in human-readable formats.
- Formatting and printing results with color coding for easier readability.
- Resolving dates using `dateparser` and AI-based generation.
- Supporting historical dates and future events resolution.

Dependencies:
- `socket`: For network communication.
- `datetime`: For working with date and time objects.
- `decimal`: For precise time calculations.
- `ntplib`: For querying time from NTP servers.
- `dateparser`: For parsing date strings.
- `colorama`: For styling the output with colors.
- `utms`: For constants related to time units and their conversions.

Functions:
- `get_ntp_time()`: Fetches the current time from an NTP server.
- `get_current_time_ntp()`: Returns the current NTP time as a UTC datetime object.
- `calculate_total_time_seconds()`: Computes the total time elapsed since the Big Bang.
- `calculate_upc()`: Calculates the Universal Planck Count.
- `return_old_time_breakdown()`: Converts time into a human-readable breakdown (years, days, etc.).
- `return_time_breakdown()`: Converts time into various scientific units (petaseconds, etc.).
- `print_results()`: Prints time breakdown in both human-readable and scientific units.
- `resolve_date_dateparser()`: Resolves a date using the `dateparser` library.
- `resolve_date()`: Resolves a date using `dateparser` and AI generation as a fallback.
- `print_datetime()`: Prints time in various formats (CE, Millennium, Unix, UPC, etc.).
- `print_header()`: Prints a header with cyan and bright styling.
- `old_unit()`: Applies magenta styling to a unit string.
- `new_unit()`: Applies green styling to a unit string.

Example usage:
    - Fetch current NTP time: `get_ntp_time()`
    - Convert time to UTC: `get_current_time_ntp()`
    - Calculate UPC: `calculate_upc()`
    - Print time breakdowns: `print_results(total_seconds)`
    - Resolve a date string: `resolve_date("2024-12-14")`

Notes:
- The module applies different color styles (using `colorama`) to improve the display of time
  breakdowns and units.
- Date parsing includes fallback to AI-based date generation if parsing fails.
"""

import socket
from datetime import datetime, timezone
from decimal import Decimal
from time import time
from typing import Optional, Union

import dateparser
import ntplib
from colorama import Fore, Style, init

from utms import constants
from utms.ai import ai_generate_date
from utms.anchors import AnchorManager

init()


# Function to get time via NTP
def get_ntp_time() -> float:
    """
    Retrieves the current time from an NTP (Network Time Protocol) server.

    This function queries an NTP server (default is "pool.ntp.org") to
    get the accurate current time.  If the NTP request is successful,
    it returns the transmit timestamp as a float. If the NTP request
    fails (due to network issues or other errors), the function falls
    back to returning the system time.

    Args:
        None: This function does not take any arguments.

    Returns:
        float: The current time, either from the NTP server (as a
        float timestamp) or the system time (as a fallback).

    Exceptions:
        - If the NTP request fails, the system time is returned instead.
    """
    client = ntplib.NTPClient()
    try:
        # Query an NTP server
        response = client.request("pool.ntp.org", version=3)
        return float(response.tx_time)  # Return the transmit timestamp
    except (ntplib.NTPException, socket.error, OSError) as e:  # pragma: no cover
        print(f"Error fetching NTP time: {e}")
        return float(time())  # Fallback to system time


# Function to calculate the current NTP time as a datetime object
def get_current_time_ntp() -> datetime:
    """
    Retrieves the current NTP time and converts it to a UTC datetime object.

    This function fetches the current time from an NTP (Network Time
    Protocol) server by calling `get_ntp_time()`, which returns a
    timestamp. The timestamp is then converted to a `datetime` object
    in UTC timezone using `datetime.fromtimestamp()`.

    Args:
        None: This function does not take any arguments.

    Returns:
        datetime: The current time as a `datetime` object in UTC.

    Exceptions:
        - If `get_ntp_time()` encounters an error, it will return the
        system time, which will be converted to a UTC `datetime`
        object.
    """
    ntp_timestamp = get_ntp_time()
    return datetime.fromtimestamp(ntp_timestamp, timezone.utc)  # Convert to UTC datetime


def return_old_time_breakdown(years: int, days: int, hours: int, minutes: int, seconds: int) -> str:
    """
    Converts a time breakdown into a human-readable string using
    custom unit names.

    This function takes individual time components (years, days,
    hours, minutes, and seconds) and creates a formatted string that
    describes the total time in a human-readable format. The string
    includes only non-zero components and uses a custom unit name for
    each time unit via the `old_unit` function.

    If all components are zero, the function returns a string
    indicating zero time in "Seconds".

    Args:
        years (int): The number of years in the time breakdown.
        days (int): The number of days in the time breakdown.
        hours (int): The number of hours in the time breakdown.
        minutes (int): The number of minutes in the time breakdown.
        seconds (int): The number of seconds in the time breakdown.

    Returns:
        str: A formatted string representing the time breakdown with
        custom unit names for each non-zero component.

    Example:
        >>> return_old_time_breakdown(2, 3, 4, 5, 6)
        '2 Years, 3 Days, 4 Hours, 5 Minutes, 6 Seconds'

    Exceptions:
        - This function assumes that the input values are non-negative
          integers representing the components of the time breakdown.
    """
    # Check if all values are zero
    if years == 0 and days == 0 and hours == 0 and minutes == 0 and seconds == 0:
        return f"0 {old_unit('Seconds')}"

    # Create the breakdown
    breakdown = []

    if years > 0:
        breakdown.append(f"{years} {old_unit('Years')}")
    if days > 0:
        breakdown.append(f"{days} {old_unit('Days')}")
    if hours > 0:
        breakdown.append(f"{hours} {old_unit('Hours')}")
    if minutes > 0:
        breakdown.append(f"{minutes} {old_unit('Minutes')}")
    if seconds > 0:
        breakdown.append(f"{seconds} {old_unit('Seconds')}")

    return ", ".join(breakdown)


def return_time_breakdown(
    integer_petaseconds: int,
    integer_teraseconds: int,
    integer_gigaseconds: int,
    integer_megaseconds: int,
    integer_kiloseconds: int,
    remaining_seconds: int,
) -> str:
    """
    Converts a time breakdown into a human-readable string with custom units.

    This function takes individual time components (petaseconds,
    teraseconds, gigaseconds, megaseconds, kiloseconds, and remaining
    seconds) and creates a formatted string describing the total time
    in a human-readable format.  The string includes only non-zero
    components, using custom unit names for each time unit via the
    `new_unit` function.

    If all components are zero, the function returns a string
    indicating zero time in "Sec".

    Args:
        integer_petaseconds (int): The number of petaseconds in the time breakdown.
        integer_teraseconds (int): The number of teraseconds in the time breakdown.
        integer_gigaseconds (int): The number of gigaseconds in the time breakdown.
        integer_megaseconds (int): The number of megaseconds in the time breakdown.
        integer_kiloseconds (int): The number of kiloseconds in the time breakdown.
        remaining_seconds (int): The remaining number of seconds in the time breakdown.

    Returns:
        str: A formatted string representing the time breakdown with
        custom unit names for each non-zero component.

    Example:
        >>> return_time_breakdown(2, 3, 4, 5, 6, 7)
        '2 PSec, 3 TSec, 4 GSec, 5 MSec, 6 KSec, 7 Sec'

    Exceptions:
        - This function assumes that the input values are non-negative
          integers representing the components of the time breakdown.
    """
    # Check if all values are zero
    if (
        integer_petaseconds == 0
        and integer_teraseconds == 0
        and integer_gigaseconds == 0
        and integer_megaseconds == 0
        and integer_kiloseconds == 0
        and remaining_seconds == 0
    ):
        return f"0 {new_unit('Sec')}"

    # Create the breakdown
    breakdown = []

    if integer_petaseconds > 0:
        breakdown.append(f"{integer_petaseconds} {new_unit('PSec')}")
    if integer_teraseconds > 0:
        breakdown.append(f"{integer_teraseconds} {new_unit('TSec')}")
    if integer_gigaseconds > 0:
        breakdown.append(f"{integer_gigaseconds} {new_unit('GSec')}")
    if integer_megaseconds > 0:
        breakdown.append(f"{integer_megaseconds} {new_unit('MSec')}")
    if integer_kiloseconds > 0:
        breakdown.append(f"{integer_kiloseconds} {new_unit('KSec')}")
    if remaining_seconds > 0:
        breakdown.append(f"{remaining_seconds} {new_unit('Sec')}")

    return ", ".join(breakdown)


def print_results(total_seconds: Decimal) -> None:
    """
    Prints the breakdown of total time in various units and a
    human-readable format based on the total time in seconds.

    This function accepts a time duration in seconds and prints its
    equivalent in different time units, including:
    - Petaseconds (Ps), Teraseconds (Ts), Gigaseconds (Gs), Megaseconds (Ms), Kiloseconds (ks)
    - A human-readable breakdown in years, days, hours, minutes, and seconds.

    The time is formatted with appropriate color coding for positive
    (green) or negative (red) values.

    The function is flexible and can be reused for any time duration,
    including specialized durations like the Universal Planck Count
    (UPC).

    Args:
        total_seconds (Decimal): The total time in seconds to be
        broken down and printed in various units.

    Returns:
        None: This function prints the time breakdown to the console.

    Example:
        >>> print_results(12345678901234)
        '+ 12345678901234 PSec, 0 TSec, 0 GSec, 0 MSec, 0 KSec, 12345678901234 Sec'
        '+ 392 Years, 5 Days, 0 Hours, 15 Minutes, 34 Seconds'

    Exceptions:
        - This function assumes that the input `total_seconds` is a
          valid `Decimal` representing the total time in seconds.
    """

    if total_seconds < 0:
        prefix = Fore.RED + Style.BRIGHT + "  - " + Style.RESET_ALL
        total_seconds = -total_seconds
    else:
        prefix = Fore.GREEN + Style.BRIGHT + "  + " + Style.RESET_ALL

    # Breakdown of total time into integer units
    remaining_seconds = int(total_seconds)
    integer_petaseconds = remaining_seconds // int(1e15)
    remaining_seconds %= int(1e15)
    integer_teraseconds = remaining_seconds // int(1e12)
    remaining_seconds %= int(1e12)
    integer_gigaseconds = remaining_seconds // int(1e9)
    remaining_seconds %= int(1e9)
    integer_megaseconds = remaining_seconds // int(1e6)
    remaining_seconds %= int(1e6)
    integer_kiloseconds = remaining_seconds // int(1e3)
    remaining_seconds %= int(1e3)

    # Human-readable breakdown of the time (in years, days, hours, minutes, seconds)
    years = int(total_seconds // int(constants.SECONDS_IN_YEAR))
    remaining_seconds_in_year = int(total_seconds % int(constants.SECONDS_IN_YEAR))
    days = remaining_seconds_in_year // (60 * 60 * 24)
    remaining_seconds_in_year %= 60 * 60 * 24
    hours = remaining_seconds_in_year // (60 * 60)
    remaining_seconds_in_year %= 60 * 60
    minutes = remaining_seconds_in_year // 60
    seconds = remaining_seconds_in_year % 60

    # Print petaseconds, teraseconds, etc.
    print(
        prefix
        + return_time_breakdown(
            integer_petaseconds,
            integer_teraseconds,
            integer_gigaseconds,
            integer_megaseconds,
            integer_kiloseconds,
            remaining_seconds,
        )
    )

    # Print years, days, hours, minutes, seconds
    print(prefix + return_old_time_breakdown(years, days, hours, minutes, seconds))


def resolve_date_dateparser(input_text: str) -> Optional[datetime]:
    """
    Parses a string representing a date and returns the corresponding
    UTC datetime object.

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
        print(parsed_date)
        utc_date = parsed_date.astimezone(timezone.utc)
        return utc_date

    return None


# Function to resolve dates
def resolve_date(input_text: str) -> Union[datetime, Decimal, None]:
    """
    Resolves a date from a given string input. The function first
    attempts to parse the date using `dateparser`, and if unsuccessful,
    it uses an AI-based approach to generate a potential date.

    The function supports:

    - Parsing valid dates from input text (via `dateparser`).
    - Handling historical dates expressed as negative years (e.g., '-44' for 44 BCE).
    - Interpreting future events expressed with a '+' sign (e.g., '+10' for 10 years from now).
    - Processing ISO 8601 formatted dates returned by the AI.

    Args:
        input_text (str): The input string representing the date to resolve.
            The input can be in formats compatible with `dateparser` or in special
            formats (e.g., BCE or future years).

    Returns:
        Union[datetime, Decimal, None]:
            - `datetime` object if a valid date is resolved.
            - `Decimal` representing seconds for future events or years before the common era.
            - `None` if the date cannot be resolved.

    Raises:
        ValueError: If both `dateparser` and the AI approach fail to resolve a date.

    Example:
        >>> resolve_date("2024-12-11")
        datetime.datetime(2024, 12, 11, 0, 0, tzinfo=datetime.timezone.utc)

        >>> resolve_date("-44")  # 44 BCE
        Decimal('-69422400000')

        >>> resolve_date("+10")  # 10 years from now
        Decimal('315569520')

    Notes:
        - The function first attempts to parse the date using the `resolve_date_dateparser`
          function. If that fails, it invokes the AI-based date generator.
        - The AI response is expected to be one of:
            - A valid ISO 8601 date string.
            - A negative number representing historical years (BCE).
            - A positive number indicating future years (converted to seconds).
        - Historical dates are converted into seconds using a year-based approximation
          or ISO 8601 representation when available.
        - Future dates are expressed in seconds from the current time.
    """
    # First, try to parse using dateparser
    resolved_date = resolve_date_dateparser(input_text)
    if resolved_date:
        return resolved_date

    # If parsing fails, fallback to AI
    ai_result = ai_generate_date(input_text)
    if ai_result == "UNKNOWN":
        raise ValueError(f"Unable to resolve date for input: {input_text}")

    # Handle AI response for historical dates
    if ai_result.startswith("-"):
        if ai_result.count("-") == 3:  # -YYYY-MM-DD
            epoch = constants.UNIX_DATE
            bc_date = datetime.strptime(ai_result, "-%Y-%m-%d")
            delta_years = epoch.year + abs(bc_date.year) - 1
            delta_days = (epoch - epoch.replace(year=epoch.year, month=1, day=1)).days
            return -Decimal((delta_years * Decimal(365.25) + delta_days) * constants.SECONDS_IN_DAY)
        # -YYYYYYYY or -1.5e9
        epoch = constants.UNIX_DATE
        return -Decimal(
            Decimal(epoch.year + abs(Decimal(ai_result)) - 1) * constants.SECONDS_IN_YEAR
        )

    # Handle AI response for future events
    if ai_result.startswith("+"):
        return Decimal(Decimal(ai_result) * constants.SECONDS_IN_YEAR)
    try:
        # If the AI produces a valid ISO 8601 timestamp
        return datetime.fromisoformat(ai_result)
    except ValueError:  # pragma: no cover
        return None


def print_datetime(timestamp: datetime, anchors: AnchorManager) -> None:
    """
    Prints the time-related calculations for a given timestamp in various formats:
    'CE Time', 'Millenium Time', 'Now Time', 'UPC Time', and 'Life Time'.
    Args:
        timestamp (datetime): The input timestamp (in UTC) to be used for the calculations.
    Returns:
        None: This function prints out the results of various time calculations.
    Example:
        >>> timestamp = datetime(2023, 1, 1, tzinfo=timezone.utc)
        >>> print_datetime(timestamp)
        # This will print time calculations based on the provided timestamp.
    """
    # total_seconds = years from UNIX time in seconds
    total_seconds = Decimal(timestamp.timestamp())

    for anchor in anchors:
        print_header(anchor.full_name)
        print_results(total_seconds - anchor.value)


def print_decimal_timestamp(total_seconds: Decimal, anchors: AnchorManager) -> None:
    """
    Prints the results of time-related calculations for a given total seconds value
    in various formats based on predefined anchors.

    The function iterates through a collection of time anchors, calculates the difference
    between the given total seconds and the anchor values, and prints the formatted results.

    :param total_seconds:
        The total number of seconds as a Decimal value, typically representing
        elapsed time since the UNIX epoch or a custom time calculation.
    :return:
        None. This function directly prints results for each anchor.

    **Example**:

    .. code-block:: python

        from decimal import Decimal

        total_seconds = Decimal("1672531200")  # Seconds for 2023-01-01 00:00:00 UTC
        print_decimal_timestamp(total_seconds)

    **Output**:

    .. code-block:: text

        CE Time
        <calculated difference>

        Millenium Time
        <calculated difference>

        Now Time
        <calculated difference>

        Life Time
        <calculated difference>
    """
    for anchor in anchors:
        print_header(anchor.full_name)
        print_results(total_seconds - anchor.value)


def print_header(header: str) -> None:
    """
    Prints the given header in cyan color with bright styling.
    Args:
        header (str): The header text to be printed.
    Returns:
        None: This function only prints the header with styling and has no return value.
    Example:
        >>> print_header("Important Notice")
        # This will print "Important Notice" in cyan with bright styling.
    """
    print(Fore.CYAN + Style.BRIGHT + header + Style.RESET_ALL)


def old_unit(unit: str) -> str:
    """
    Applies magenta color styling to the given unit string.
    Args:
        unit (str): The unit name to be styled.
    Returns:
        str: The unit name wrapped in magenta color styling.
    Example:
        >>> old_unit("Seconds")
        # This will return the string "Seconds" in magenta color.
    """
    return str(Fore.MAGENTA) + unit + str(Style.RESET_ALL)


def new_unit(unit: str) -> str:
    """
    Applies green color styling to the given unit string.
    Args:
        unit (str): The unit name to be styled.
    Returns:
        str: The unit name wrapped in green color styling.
    Example:
        >>> new_unit("Years")
        # This will return the string "Years" in green color.
    """
    return str(Fore.GREEN) + unit + str(Style.RESET_ALL)
