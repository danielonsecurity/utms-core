from utms.core.time.utils import calculate_decimal_time, calculate_standard_time

from prettytable import PrettyTable
from .colors import ColorFormatter

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
