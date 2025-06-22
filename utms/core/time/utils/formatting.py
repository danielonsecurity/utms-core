from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional, Union

import hy
from colorama import Fore, Style, init
from prettytable import PrettyTable

if TYPE_CHECKING:
    from utms.config import Config

from utms.core.time.plt import seconds_to_hplt, seconds_to_pplt
from utms.utils.display.colors import ColorFormatter

init()


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
    total_seconds = Decimal(timestamp.timestamp()) if isinstance(timestamp, datetime) else timestamp

    # Get anchor list
    anchor_list = (
        config.anchors.get_anchors_by_group("default")
        if not anchors
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
                        format_specs.append({hy.models.Keyword("units"): value.split(",")})
                else:
                    # Handle predefined formats
                    format_specs.append(format_spec)
            anchor._formats = format_specs

    # Print results for each anchor
    for anchor in anchor_list:
        print(ColorFormatter.cyan(f"{config.anchors.get_anchor(anchor)}: {anchor.name}"))

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
