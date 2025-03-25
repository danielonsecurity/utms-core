from decimal import Decimal

from .colors import ColorFormatter


def color_scientific_format(number_str: str) -> str:
    """Format scientific notation string with colored 'e' and '+/-' symbols."""
    # Split the string at 'e'
    parts = number_str.split("e")
    if len(parts) != 2:
        return number_str  # Return unchanged if not in scientific notation

    base, exponent = parts
    # Handle the sign in the exponent
    sign = ""
    if exponent.startswith("+") or exponent.startswith("-"):
        sign = exponent[0]
        exponent = exponent[1:]

    # Construct the colored string
    return f"{base}" f"{ColorFormatter.magenta('e')}" f"{ColorFormatter.red(sign)}" f"{exponent}"


def format_value(
    value: Decimal, threshold: Decimal = Decimal("1e7"), small_threshold: Decimal = Decimal("0.001")
) -> str:
    def apply_red_style(value: str) -> str:
        """Applies bright red style to the formatted value."""
        return ColorFormatter.bright_red(value)

    def apply_green_style(value: str) -> str:
        """Applies bright green style to the formatted value."""
        return ColorFormatter.bright_green(value)

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
