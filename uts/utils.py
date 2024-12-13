"""
This module contains most of the functions needed for time operations.
"""

import socket
from datetime import datetime, timezone
from decimal import Decimal
from time import time
from typing import Optional, Tuple, Union

import dateparser
import ntplib
from colorama import Fore, Style, init

from uts import constants
from uts.ai import ai_generate_date

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
    except (ntplib.NTPException, socket.error, OSError) as e:
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


# Function to calculate the total time since the Big Bang in seconds
def calculate_total_time_seconds() -> Decimal:
    """
    Calculates the total time elapsed since the Big Bang in seconds.

    This function calculates the total time by adding the current NTP
    time (in seconds) to the known age of the universe, which is
    provided in years (multiplied by the number of seconds in a year).
    The result is returned as a `Decimal` to maintain precision.

    Args:
        None: This function does not take any arguments.

    Returns:
        Decimal: The total time since the Big Bang, in seconds.

    Exceptions:
        - This function relies on `get_ntp_time()` to fetch the
          current time, and will return a total time based on the
          system's NTP time if the server request fails.
    """
    current_timestamp_seconds = Decimal(get_ntp_time())
    age_of_universe_seconds = constants.AGE_OF_UNIVERSE_YEARS * constants.SECONDS_IN_YEAR
    return age_of_universe_seconds + current_timestamp_seconds


# Function to calculate UPC (Universal Planck Count)
def calculate_upc() -> Decimal:
    """
    Calculates the Universal Planck Count (UPC).

    This function computes the UPC by dividing the total time since
    the Big Bang (in seconds) by the Planck time, which is a
    fundamental physical constant. The result is returned as a
    `Decimal` to maintain precision.

    Args:
        None: This function does not take any arguments.

    Returns:
        Decimal: The Universal Planck Count (UPC), representing the
        total time since the Big Bang divided by the Planck time.

    Exceptions:
        - This function depends on `calculate_total_time_seconds()`,
          so any error in fetching or calculating the total time
          (e.g., due to NTP issues) will affect the UPC calculation.
    """
    return calculate_total_time_seconds() / constants.PLANCK_TIME_SECONDS


# Function to convert total time into larger units
def convert_time_units(
    total_time_seconds: Decimal,
) -> Tuple[Decimal, Decimal, Decimal, Decimal, Decimal]:
    """
    Converts total time in seconds into larger time units.

    This function takes a time duration in seconds and converts it
    into the following larger time units:
    - Kiloseconds (ks)
    - Megaseconds (Ms)
    - Gigaseconds (Gs)
    - Teraseconds (Ts)
    - Petaseconds (Ps)

    The conversion is done by dividing the total time in seconds by
    the appropriate power of 10.

    Args:
        total_time_seconds (Decimal): The time duration in seconds to
        be converted into larger units.

    Returns:
        Tuple[Decimal, Decimal, Decimal, Decimal, Decimal]: A tuple
        containing the converted time values in kiloseconds,
        megaseconds, gigaseconds, teraseconds, and petaseconds, in
        that order.

    Exceptions:
        - This function does not explicitly raise exceptions but
          assumes the input `total_time_seconds` is a valid `Decimal`
          representing the total time in seconds.
    """
    kiloseconds = total_time_seconds / Decimal("1e3")
    megaseconds = total_time_seconds / Decimal("1e6")
    gigaseconds = total_time_seconds / Decimal("1e9")
    teraseconds = total_time_seconds / Decimal("1e12")
    petaseconds = total_time_seconds / Decimal("1e15")
    return kiloseconds, megaseconds, gigaseconds, teraseconds, petaseconds


# Function to break down time into integer units
def breakdown_time(
    total_time_seconds: Decimal,
) -> Tuple[int, int, int, int, int, int]:
    """
    Breaks down a total time in seconds into integer units of larger time units.

    This function takes a time duration in seconds and breaks it down
    into the following integer units:
    - Petaseconds (Ps)
    - Teraseconds (Ts)
    - Gigaseconds (Gs)
    - Megaseconds (Ms)
    - Kiloseconds (ks)
    - Remaining seconds

    The function calculates how many whole units of each time category
    can fit into the total time, and returns the breakdown in each
    unit, along with the remaining seconds.

    Args:
        total_time_seconds (Decimal): The total time in seconds to be
        broken down into integer units.

    Returns:
        Tuple[int, int, int, int, int, int]: A tuple containing the
        breakdown of the total time in the following order:
        petaseconds, teraseconds, gigaseconds, megaseconds,
        kiloseconds, and the remaining seconds.

    Exceptions:
        - This function assumes that the input `total_time_seconds` is
          a valid `Decimal` representing the total time in seconds.
    """
    remaining_seconds = int(total_time_seconds)

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

    return (
        integer_petaseconds,
        integer_teraseconds,
        integer_gigaseconds,
        integer_megaseconds,
        integer_kiloseconds,
        remaining_seconds,
    )


# Function to convert total time into years, days, hours, minutes, seconds
def human_readable_time(
    total_time_seconds: int,
) -> Tuple[int, int, int, int, int]:
    """
    Converts total time in seconds into a human-readable format
    (years, days, hours, minutes, seconds).

    This function takes a total time duration in seconds and breaks it
    down into its equivalent in years, days, hours, minutes, and
    seconds. The conversion is based on the number of seconds in a
    year (as defined by `constants.SECONDS_IN_YEAR`).

    Args:
        total_time_seconds (int): The total time in seconds to be
        converted into a human-readable format.

    Returns:
        Tuple[int, int, int, int, int]: A tuple containing the
        breakdown of the total time in the following order: years,
        days, hours, minutes, and seconds.

    Exceptions:
        - This function assumes that the input `total_time_seconds` is
          a valid integer representing the total time in seconds.
    """
    years = int(total_time_seconds // int(constants.SECONDS_IN_YEAR))
    remaining_seconds_in_year = int(total_time_seconds % int(constants.SECONDS_IN_YEAR))
    days = remaining_seconds_in_year // (60 * 60 * 24)
    remaining_seconds_in_year %= 60 * 60 * 24
    hours = remaining_seconds_in_year // (60 * 60)
    remaining_seconds_in_year %= 60 * 60
    minutes = remaining_seconds_in_year // 60
    seconds = remaining_seconds_in_year % 60
    return years, days, hours, minutes, seconds


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


def print_all_conversions() -> None:
    """
    Prints all available time conversion tables.

    This function prints three different time conversion tables:
    - A standard conversion table (`print_conversion_table`)
    - A reversed conversion table (`print_reversed_conversion_table`)
    - A concise conversion table (`print_concise_conversion_table`)

    The function provides a comprehensive set of time conversions for
    different use cases and displays them sequentially.

    Args:
        None: This function does not accept any arguments.

    Returns:
        None: This function prints the conversion tables directly to the console.

    Example:
        >>> print_all_conversions()
        Prints all three conversion tables to the console.

    Exceptions:
        - This function assumes that the respective functions for
          printing conversion tables (`print_conversion_table`,
          `print_reversed_conversion_table`, and
          `print_concise_conversion_table`) are defined and callable.
    """
    print_conversion_table()
    print_reversed_conversion_table()
    print_concise_conversion_table()


def format_unit_output(unit: str, *values: tuple[str, Decimal, int]) -> str:
    """
    Helper function to format unit output with alignment.

    Args:
        unit: The unit string.
        values: Tuples of (label, value, precision) to format.

    Returns:
        Formatted string for printing.
    """
    formatted_values = ", ".join(
        f"{value:.{precision}f} {label}" for label, value, precision in values
    )
    return f"{unit:<20} {formatted_values}"


def print_concise_conversion_table() -> None:
    """
    Prints a concise time conversion table that displays the
    relationship between various time units.

    This function generates and prints a table of time units, including:
    - Kiloseconds (KSec), Megaseconds (MSec), Gigaseconds (GSec),
      Teraseconds (TSec), and Petaseconds (PSec)
    - The corresponding conversions to larger units such as minutes,
      hours, days, weeks, months, and years for each unit
    - The time breakdown for human-readable time units like hours,
      days, weeks, months, years, centuries, and millennia.

    Each unit's conversion is displayed with different levels of
    precision for clarity, and the output is formatted into a neatly
    aligned table.

    Args:
        None: This function does not accept any arguments.

    Returns:
        None: This function prints the concise conversion table directly to the console.

    Example:
        >>> print_concise_conversion_table()
        Prints a concise table with conversions for KSec, MSec, GSec, TSec, and PSec.

    Exceptions:
        - This function assumes that `constants.TIME_UNITS` and
          `constants.HUMAN_TIME_UNITS` are defined and contain valid
          unit values.
        - This function also relies on the `format_unit_output`
          function to format the unit conversions.
    """
    print(f"{'Time Unit':<20}{'Relevant Units':<50}")
    print("-" * 70)

    # Process constants.TIME_UNITS
    for unit, factor in constants.TIME_UNITS.items():
        seconds = factor
        minutes = seconds / constants.SECONDS_IN_MINUTE
        hours = seconds / constants.SECONDS_IN_HOUR
        days = seconds / constants.SECONDS_IN_DAY
        weeks = seconds / constants.SECONDS_IN_WEEK
        months = seconds / constants.SECONDS_IN_MONTH
        years = seconds / constants.SECONDS_IN_YEAR

        if unit == "Kilosecond (KSec)":
            print(
                format_unit_output(
                    unit, ("minutes", minutes, 3), ("hours", hours, 3), ("days", days, 3)
                )
            )
        elif unit == "Megasecond (MSec)":
            print(
                format_unit_output(
                    unit,
                    ("hours", hours, 2),
                    ("days", days, 2),
                    ("weeks", weeks, 2),
                    ("months", months, 2),
                    ("years", years, 2),
                )
            )
        elif unit == "Gigasecond (GSec)":
            print(
                format_unit_output(
                    unit,
                    ("days", days, 1),
                    ("weeks", weeks, 1),
                    ("months", months, 1),
                    ("years", years, 1),
                )
            )
        elif unit == "Terasecond (TSec)":
            print(
                format_unit_output(
                    unit, ("years", years, 1), ("centuries", years / Decimal(100), 1)
                )
            )
        elif unit == "Petasecond (PSec)":
            print(
                format_unit_output(
                    unit,
                    ("years", years, 0),
                    ("centuries", years / Decimal(100), 0),
                    ("millennia", years / Decimal(1000), 0),
                )
            )

    print("-" * 70)

    # Process constants.HUMAN_TIME_UNITS
    for unit, factor in constants.HUMAN_TIME_UNITS.items():
        values = [("KSec", factor / Decimal("1e3"), 3)]

        if unit in {"1 Hour", "1 Day", "1 Week", "1 Month", "1 Year"}:
            values.append(("MSec", factor / Decimal("1e6"), 3))
        if unit in {"1 Week", "1 Month", "1 Year", "1 Century", "1 Millennium"}:
            values.append(("GSec", factor / Decimal("1e9"), 3))
        if unit in {"1 Century", "1 Millennium"}:
            values.append(("TSec", factor / Decimal("1e12"), 3))

        print(format_unit_output(unit, *values))

    print()


def format_reversed_row(row: list[str]) -> str:
    """
    Helper function to format a row for reversed conversion table.

    Args:
        row: List of row values.

    Returns:
        Formatted string for printing.
    """
    return f"{row[0]:<20}{row[1]:<20}{row[2]:<20}{row[3]:<20}{row[4]:<20}{row[5]}"


def format_reversed_header(units: list[str]) -> str:
    """
    Helper function to format the header for reversed conversion table.

    Args:
        units: List of unit headers.

    Returns:
        Formatted string for printing.
    """
    return "".join(f"{unit:<20}" for unit in units)


def print_reversed_conversion_table() -> None:
    """
    Prints a reversed time conversion table that displays the
    relationship between human-readable time units and UTS time units.

    This function generates and prints a table where human time units
    (e.g., hours, days, months, years) are converted to the following
    UTS (Universal Time Scale) units:
    - Kiloseconds (KSec), Megaseconds (MSec), Gigaseconds (GSec),
      Teraseconds (TSec), and Petaseconds (PSec).

    The table presents each human-readable unit alongside its
    conversion to UTS time units, displaying the values with six
    decimal places of precision.

    Args:
        None: This function does not accept any arguments.

    Returns:
        None: This function prints the reversed conversion table directly to the console.

    Example:
        >>> print_reversed_conversion_table()
        Prints a reversed table with human time units converted to UTS time units.

    Exceptions:
        - This function assumes that `constants.HUMAN_TIME_UNITS` and
          `constants.TIME_UNITS` are defined and contain valid unit
          values.
        - This function also relies on the `format_reversed_header`
          and `format_reversed_row` functions to format the table
          output.
    """
    header_units = [
        "Time Units",
        "Kiloseconds (KSec)",
        "Megaseconds (MSec)",
        "Gigaseconds (GSec)",
        "Teraseconds (TSec)",
        "Petaseconds (PSec)",
    ]
    print(format_reversed_header(header_units))
    print("-" * 120)

    # Iterate over human time units and convert to UTS
    for unit, seconds in constants.HUMAN_TIME_UNITS.items():
        row = [unit]  # Start with the time unit label

        # Convert to each UTS time unit
        for uts_factor in constants.TIME_UNITS.values():
            uts_value = seconds / uts_factor
            row.append(f"{uts_value:.6f}")

        # Print the row with appropriate formatting
        print(format_reversed_row(row))
    print()


def print_conversion_table() -> None:
    """
    Prints a time conversion table that displays the relationship between various time units.

    This function generates and prints a table with different time
    units (e.g., Kiloseconds, Megaseconds, Gigaseconds) and their
    equivalent values in seconds, minutes, hours, days, weeks, months,
    years, centuries, and millennia.

    The table includes the following columns:
    - Time Unit: The name of the time unit (e.g., Kilosecond, Megasecond)
    - Seconds: Equivalent value in seconds
    - Minutes: Equivalent value in minutes
    - Hours: Equivalent value in hours
    - Days: Equivalent value in days
    - Weeks: Equivalent value in weeks
    - Months: Equivalent value in months
    - Years: Equivalent value in years
    - Centuries: Equivalent value in centuries
    - Millennia: Equivalent value in millennia

    Args:
        None: This function does not accept any arguments.

    Returns:
        None: This function prints the time conversion table directly to the console.

    Example:
        >>> print_conversion_table()
        Prints a table showing conversions from various time units to
        other standard time units.

    Exceptions:
        - This function assumes that `constants.TIME_UNITS`,
          `constants.SECONDS_IN_MINUTE`, `constants.SECONDS_IN_HOUR`,
          `constants.SECONDS_IN_DAY`, `constants.SECONDS_IN_WEEK`,
          `constants.SECONDS_IN_MONTH`, `constants.SECONDS_IN_YEAR`,
          `constants.SECONDS_IN_CENTURY`, and
          `constants.SECONDS_IN_MILLENNIUM` are defined and contain
          valid numerical values.
    """

    header_units = [
        "Time Unit",
        "Seconds",
        "Minutes",
        "Hours",
        "Days",
        "Weeks",
        "Months",
        "Years",
        "Centuries",
        "Millennium",
    ]
    print("".join(f"{unit:<20}" for unit in header_units))
    print("-" * 200)

    # Loop through each unit and calculate conversions
    for unit, factor in constants.TIME_UNITS.items():
        seconds = factor
        minutes = seconds / constants.SECONDS_IN_MINUTE
        hours = seconds / constants.SECONDS_IN_HOUR
        days = seconds / constants.SECONDS_IN_DAY
        weeks = seconds / constants.SECONDS_IN_WEEK
        months = seconds / constants.SECONDS_IN_MONTH
        years = seconds / constants.SECONDS_IN_YEAR
        centuries = seconds / constants.SECONDS_IN_CENTURY
        millennia = seconds / constants.SECONDS_IN_MILLENNIUM

        print(
            f"{unit:<25}{seconds:<20.0f}{minutes:<20.3f}{hours:<20.3f}{days:<20.3f}"
            f"{weeks:<20.3f}{months:<20.3f}{years:<20.3f}{centuries:<20.3f}{millennia:<20.3f}"
        )
    print()


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
        # Ensure the date is timezone-aware and in UTC
        if parsed_date.tzinfo is None:
            parsed_date = parsed_date.replace(tzinfo=timezone.utc)
        utc_date = parsed_date.astimezone(timezone.utc)
        return utc_date

    return None


# Function to resolve dates
def resolve_date(input_text: str) -> Union[datetime, str, int]:
    """
    Resolves a date from a given string input. This function first
    attempts to parse the date using `dateparser`, and if that fails,
    it falls back to generating a date via an AI-based approach.

    The function can handle:
    - A valid date parsed from the input text (using `dateparser`).
    - Historical dates expressed as negative years (e.g., '-44' for 44 BCE).
    - Future events expressed with a '+' sign (e.g., '+10' for 10 years from now).
    - ISO 8601 formatted dates returned by the AI.

    Args:
        input_text (str): The input string containing the date to
                          resolve. It could be any date expression in
                          a format supported by `dateparser` or the AI
                          response.

    Returns:
        Union[datetime, str, int]:
            - A `datetime` object if a valid date is resolved.
            - A string "UNKNOWN" if the date cannot be resolved.
            - An integer representing the number of seconds for future
              events, or years before the current era for historical
              events.

    Raises:
        ValueError: If the date cannot be resolved (both `dateparser` and AI approaches fail).

    Example:
        >>> resolve_date("2024-12-11")
        datetime.datetime(2024, 12, 11, 0, 0, tzinfo=datetime.timezone.utc)

        >>> resolve_date("44 BCE")
        datetime.datetime(1, 1, 1, tzinfo=datetime.timezone.utc)

        >>> resolve_date("+10")
        315569520

    Notes:
        - This function first attempts to resolve the date using
          `resolve_date_dateparser` and falls back to AI if that
          fails.
        - The AI response should be an ISO 8601 date string, a
          negative number representing historical years (BCE), or a
          positive number indicating future years (in seconds).
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
        years_before_ce = int(ai_result)  # Example: '-44' -> -44 years
        resolved_date = datetime(1, 1, 1, tzinfo=timezone.utc).replace(year=1 + years_before_ce)
        return resolved_date

    # Handle AI response for future events
    if ai_result.startswith("+"):
        return int(ai_result)

    # If the AI produces a valid ISO 8601 timestamp
    return datetime.fromisoformat(ai_result)


def print_time(timestamp: datetime) -> None:
    """
    Prints the time-related calculations for a given timestamp in various formats:
    'CE Time', 'Millenium Time', 'Now Time', 'UPC Time', and 'Life Time'.

    Args:
        timestamp (datetime): The input timestamp (in UTC) to be used for the calculations.

    Returns:
        None: This function prints out the results of various time calculations.

    Example:
        >>> timestamp = datetime(2023, 1, 1, tzinfo=timezone.utc)
        >>> print_time(timestamp)
        # This will print time calculations based on the provided timestamp.
    """
    delta = Decimal(
        (timestamp - datetime(1, 1, 1, 0, 0, tzinfo=timezone.utc)).total_seconds()
    ) + +Decimal(constants.SECONDS_IN_YEAR)
    print_header("CE Time:")
    print_results(delta)

    if timestamp >= datetime(1970, 1, 1, tzinfo=timezone.utc):
        total_seconds = Decimal(timestamp.timestamp())
    else:
        total_seconds = Decimal(
            (timestamp - datetime(1970, 1, 1, 0, 0, tzinfo=timezone.utc)).total_seconds()
        )

    delta = total_seconds - Decimal(constants.MILLENNIUM_DATE.timestamp())
    print_header("Millenium Time:")
    print_results(delta)

    delta = total_seconds - Decimal(get_current_time_ntp().timestamp())
    print_header("Now Time:")
    print_results(delta)

    delta = total_seconds - Decimal(constants.UNIX_DATE.timestamp())
    print_header("Unix Time:")
    print_results(delta)

    delta = Decimal(calculate_total_time_seconds()) + delta
    print_header("UPC Time:")
    print_results(delta)

    delta = total_seconds - Decimal(constants.LIFE_DATE.timestamp())
    print_header("Life Time:")
    print_results(delta)


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
