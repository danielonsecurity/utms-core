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
        print(ColorFormatter.cyan(f"{config.anchors.get_label(anchor)}: {anchor.name}"))

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


def format_value(
    value: Decimal, threshold: Decimal = Decimal("1e7"), small_threshold: Decimal = Decimal("0.001")
) -> str:
    """Format a numeric value based on specified thresholds, using conditional
    formatting.

    The function formats the value based on its magnitude, and applies different styles
    depending on whether the value is above or below specific thresholds.

    Args:
        value (Decimal): The numeric value to format.
        threshold (Decimal, optional): The threshold above which
        scientific notation is used. Defaults to 1e7.
        small_threshold (Decimal, optional): The threshold below which
        scientific notation with 3 decimal places is used. Defaults to
        0.001.

    Returns:
        str: The formatted string representation of the value with appropriate styles applied.

    Formatting Rules:
        - Values smaller than `small_threshold` are formatted in
          scientific notation with 3 decimal places in red.
        - Values larger than `small_threshold` but smaller than `threshold`:
            - Integer values are formatted with no decimal places in green.
            - Values greater than 1 are formatted with 5 decimal places in green.
            - Values close to zero are formatted with 3 or 5 decimal
              places in red depending on precision.
        - Values greater than or equal to `threshold` are formatted in
          scientific notation with 3 decimal places in green.
        - All formatting is left-aligned in a 33-character wide field.

    Example:
        >>> format_value(123456.789)
        '\x1b[32m\x1b[1m123456.78900\x1b[39m\x1b[22m'  # Example output with a large value

        >>> format_value(0.000000123)
        '\x1b[31m\x1b[1m1.230e-07\x1b[39m\x1b[22m'  # Example output for a small value
    """

    def apply_red_style(value: str) -> str:
        """Applies bright red style to the formatted value."""
        return f"{Style.BRIGHT}{Fore.RED}{value}{Style.RESET_ALL}"

    def apply_green_style(value: str) -> str:
        """Applies bright green style to the formatted value."""
        return f"{Style.BRIGHT}{Fore.GREEN}{value}{Style.RESET_ALL}"

    # Handle absolute value less than small_threshold
    if abs(value) < small_threshold:
        formatted_value = apply_red_style(
            f"{value:.3e}"
        )  # Scientific notation with 3 decimal places
    # Handle values smaller than threshold (1e7) but larger than small_threshold
    elif abs(value) < threshold:
        if value == value.to_integral_value():
            formatted_value = apply_green_style(f"{value:.0f}")  # Integer formatting
        elif value > 1:
            formatted_value = apply_green_style(
                f"{value:.5f}"
            )  # Fixed-point notation with 5 decimal places
        elif value == value.quantize(small_threshold):
            formatted_value = apply_red_style(
                f"{value:.3f}"
            )  # Fixed-point with 3 decimal places if no further digits
        else:
            formatted_value = apply_red_style(
                f"{value:.5f}"
            )  # Fixed-point notation with 5 decimal places
    # Handle absolute value greater than or equal to threshold
    elif abs(value) >= threshold:
        formatted_value = apply_green_style(
            f"{value:.3e}"
        )  # Scientific notation with 3 decimal places
    else:
        formatted_value = apply_green_style(
            f"{value:.3f}"
        )  # Fixed-point notation with 3 decimal places

    return formatted_value.ljust(33)
