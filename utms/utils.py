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

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Union

import dateparser
from colorama import Fore, Style, init
from prettytable import PrettyTable

from utms.config import Config

init()


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


def print_time(timestamp: "Union[datetime, Decimal]", config: Config) -> None:
    """
    Prints the time-related calculations for a given timestamp or total seconds value
    in various formats: 'CE Time', 'Millenium Time', 'Now Time', 'UPC Time', and 'Life Time'.

    The function handles both `datetime` (in UTC) or `Decimal` representing seconds since the UNIX
    epoch.

    Args:
        timestamp (Union[datetime, Decimal]): The input timestamp (in UTC) or total seconds
                                              since the UNIX epoch to be used for the calculations.
        config (Config): The configuration object containing time anchors and other settings.

    Returns:
        None: This function prints out the results of various time calculations.

    Example:
        >>> timestamp = datetime(2023, 1, 1, tzinfo=timezone.utc)
        >>> print_time_related_data(timestamp, config)
        # OR
        >>> total_seconds = Decimal("1672531200")
        >>> print_time_related_data(total_seconds, config)
    """
    # If the input is a datetime object, convert it to total seconds
    if isinstance(timestamp, datetime):
        total_seconds = Decimal(timestamp.timestamp())
    else:
        total_seconds = timestamp

    # Iterate over the anchors and print results
    for anchor in config.anchors:
        print_header(f"{config.anchors.get_label(anchor)}: {anchor.full_name}")
        print(anchor.breakdown(total_seconds - anchor.value, config.units))


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


def calculate_decimal_time(seconds: int) -> tuple[int, int, int, float]:
    """Calculate deciday, centiday, decimal seconds, and decidays as a float."""
    deciday = seconds // 8640
    centiday = (seconds % 8640) // 864
    decimal_seconds = int(seconds - centiday * 864 - deciday * 8640)
    decidays_float = seconds / 8640
    return deciday, centiday, decimal_seconds, decidays_float


def calculate_standard_time(seconds: int) -> str:
    """Calculate standard time in HH:MM:SS format."""
    total_minutes = seconds // 60
    hours = (total_minutes // 60) % 24
    minutes = total_minutes % 60
    standard_seconds = seconds - hours * 3600 - minutes * 60
    return f"{hours:02}:{minutes:02}:{standard_seconds:02}"


def format_with_color(value: str, condition: bool, color_code: str = "\033[31m") -> str:
    """Format a value with color if the condition is met."""
    reset_code = "\033[0m"
    return f"{color_code}{value}{reset_code}" if condition else value


def generate_time_table() -> str:
    """Generate a time table mapping seconds to decidays, centidays, standard time, and kiloseconds.

    Returns:
        str: Formatted table as a string.
    """
    table = PrettyTable()
    table.field_names = [
        "Decimal Time (D.C.SSS)",
        "Decidays (float)",
        "Standard Time (HH:MM:SS)",
        "Kiloseconds (86.4)",
    ]

    for seconds_since_midnight in range(86400):
        # Calculate time components
        deciday, centiday, decimal_seconds, decidays_float = calculate_decimal_time(
            seconds_since_midnight
        )
        standard_time = calculate_standard_time(seconds_since_midnight)
        kiloseconds = seconds_since_midnight / 1000

        # Check conditions for coloring
        is_decimal_red = centiday % 5 == 0 and decimal_seconds == 0
        is_standard_red = ":" in standard_time and standard_time.endswith("00:00")
        is_kiloseconds_red = kiloseconds % 10 == 0

        # Apply conditional coloring
        decimal_time_colored = format_with_color(
            f"{deciday}.{centiday}.{decimal_seconds:03}", is_decimal_red
        )
        standard_time_colored = format_with_color(standard_time, is_standard_red)
        kiloseconds_colored = format_with_color(f"{kiloseconds:.2f}", is_kiloseconds_red)
        decidays_colored = format_with_color(f"{decidays_float:.5f}", is_decimal_red)

        # Add row if any condition is satisfied
        if is_decimal_red or is_standard_red or is_kiloseconds_red:
            table.add_row(
                [
                    decimal_time_colored,
                    decidays_colored,
                    standard_time_colored,
                    kiloseconds_colored,
                ]
            )

    return str(table)


def convert_time(input_time: str) -> str:
    """
    Converts time between 24-hour format (HH:MM:SS or HH:MM) and decimal format (DD.CD.SSS or
    DD.CD).

    Args:
        input_time (str): The input time in either 24-hour format or decimal format.

    Returns:
        str: The converted time in the opposite format.
    """
    # Check if the input is in 24-hour format (HH:MM:SS or HH:MM)
    if ":" in input_time:
        return convert_to_decimal(input_time)

    # Check if the input is in decimal format (DD.CD.SSS or DD.CD)
    if "." in input_time:
        return convert_to_24hr(input_time)

    raise ValueError("Invalid time format. Use HH:MM:SS, HH:MM, DD.CD.SSS, or DD.CD.")


def convert_to_decimal(time_24hr: str) -> str:
    """
    Converts 24-hour format (HH:MM:SS or HH:MM) to decimal format (DD.CD.SSS or DD.CD).

    Args:
        time_24hr (str): The time in 24-hour format (HH:MM:SS or HH:MM).

    Returns:
        str: The time in decimal format (DD.CD.SSS or DD.CD).
    """
    # Extract hours, minutes, and optional seconds
    time_parts = time_24hr.split(":")
    hours = int(time_parts[0])
    minutes = int(time_parts[1])
    seconds = int(time_parts[2]) if len(time_parts) > 2 else 0

    # Total seconds since midnight
    total_seconds = hours * 3600 + minutes * 60 + seconds

    # Convert to decimal time
    decidays = total_seconds // 8640  # 1 deciday = 8640 seconds
    remaining_seconds = total_seconds % 8640
    centidays = remaining_seconds // 864  # 1 centiday = 864 seconds
    decimal_seconds = (remaining_seconds % 864) / 864  # The fractional part of decimal seconds

    # Format the decimal time to have one digit for centiday and optional milliseconds
    decimal_time = f"{decidays}.{centidays}.{int(decimal_seconds * 864):03}"

    return decimal_time


def convert_to_24hr(decimal_time: str) -> str:
    """
    Converts decimal format (DD.CD.SSS or DD.CD) to 24-hour format (HH:MM:SS or HH:MM).

    Args:
        decimal_time (str): The time in decimal format (DD.CD.SSS or DD.CD).

    Returns:
        str: The time in 24-hour format (HH:MM:SS or HH:MM).
    """
    # Split decimal time into deciday and centiday (and optional centisecond)
    time_parts = decimal_time.split(".")
    decidays = int(time_parts[0])
    centidays = int(time_parts[1])
    decimal_seconds = int(time_parts[2]) if len(time_parts) > 2 else 0

    # Calculate total seconds
    total_seconds = (decidays * 8640) + (centidays * 864) + decimal_seconds

    # Convert total seconds to hours, minutes, and seconds
    hours = total_seconds // 3600
    total_seconds %= 3600
    minutes = total_seconds // 60
    seconds = total_seconds % 60

    return f"{hours:02}:{minutes:02}:{seconds:02}"


def get_seconds_since_midnight() -> int:
    """
    Get the number of seconds that have passed since midnight today.
    """
    now = datetime.now(datetime.now().astimezone().tzinfo)  # Get the current local time
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    seconds_since_midnight = (now - midnight).seconds
    return seconds_since_midnight
