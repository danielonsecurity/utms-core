from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional, Union

from colorama import Fore, Style, init
from prettytable import PrettyTable

if TYPE_CHECKING:
    from utms.config import Config

from utms.core.plt import seconds_to_hplt, seconds_to_pplt

from ..time.conversion import calculate_decimal_time, calculate_standard_time
from .colors import ColorFormatter

init()


def print_row(items_list, separator="   "):
    """Prints a row of items with formatting."""
    formatted_items = []
    for items in items_list:
        formatted_items.append(f"{items}")
    print(separator.join(formatted_items))


def print_time(
    timestamp: "Union[datetime, Decimal]",
    config: "Config",
    anchors: Optional[str] = None,
    formats: Optional[str] = None,
    plt: bool = False,
) -> None:
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
    # Convert timestamp to total seconds
    total_seconds = (
        Decimal(timestamp.timestamp()) if isinstance(timestamp, datetime) 
        else timestamp
    )

    # Get anchor list
    anchor_list = (
        config.anchors.get_anchors_by_group("default") if not anchors
        else config.anchors.get_anchors_from_str(anchors)
    )
    anchor_list = list(set(anchor_list))

    # Override formats if specified
    if formats:
        for anchor in anchor_list:
            # Parse format specifications from string
            format_specs = []
            for format_spec in formats.split(";"):
                if ":" in format_spec:
                    # Handle key:value format
                    key, value = format_spec.split(":")
                    if key == "units":
                        format_specs.append({
                            hy.models.Keyword("units"): value.split(",")
                        })
                else:
                    # Handle predefined formats
                    format_specs.append(format_spec)
            anchor._formats = format_specs


    # # Override breakdowns if specified
    # if breakdowns:
    #     for anchor in anchor_list:
    #         anchor.breakdowns = [
    #             segment.split(",") 
    #             for segment in breakdowns.split(";")
    #         ]


    # Print results for each anchor
    for anchor in anchor_list:
        print(ColorFormatter.cyan(f"{config.anchors.get_label(anchor)}: {anchor.name}"))
        
        # # Print breakdowns
        # breakdown_result = anchor.breakdown(total_seconds - anchor.value, config.units)
        # if breakdown_result:
        #     print(breakdown_result)
            
        # Print formats
        format_result = anchor.format(total_seconds - anchor.value, config.units)
        if format_result:
            print(format_result)

        # Print PLT values if requested
        if plt:
            print(
                f"    {Fore.GREEN}{Style.BRIGHT}pPLT:{Style.RESET_ALL} "
                f"{seconds_to_pplt(total_seconds - anchor.value):.5f}"
            )
            print(
                f"    {Fore.GREEN}{Style.BRIGHT}hPLT:{Style.RESET_ALL} "
                f"{seconds_to_hplt(total_seconds - anchor.value):.5f}"
            )


def generate_time_table() -> str:
    """Generate a time table mapping seconds to decidays, centidays, standard
    time, and kiloseconds.

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
        decimal_time_colored = ColorFormatter.format_if(
            f"{deciday}.{centiday}.{decimal_seconds:03}", is_decimal_red, ColorFormatter.RED
        )
        standard_time_colored = ColorFormatter.format_if(
            standard_time, is_standard_red, ColorFormatter.RED
        )
        kiloseconds_colored = ColorFormatter.format_if(
            f"{kiloseconds:.2f}", is_kiloseconds_red, ColorFormatter.RED
        )
        decidays_colored = ColorFormatter.format_if(
            f"{decidays_float:.5f}", is_decimal_red, ColorFormatter.RED
        )

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
