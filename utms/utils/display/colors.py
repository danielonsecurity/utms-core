from colorama import Fore, Style, init

init()


def old_unit(unit: str) -> str:
    """Applies magenta color styling to the given unit string.

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
    """Applies green color styling to the given unit string.

    Args:
        unit (str): The unit name to be styled.
    Returns:
        str: The unit name wrapped in green color styling.
    Example:
        >>> new_unit("Years")
        # This will return the string "Years" in green color.
    """
    return str(Fore.GREEN) + unit + str(Style.RESET_ALL)


def format_with_color(value: str, condition: bool, color_code: str = "\033[31m") -> str:
    """Format a value with color if the condition is met."""
    reset_code = "\033[0m"
    return f"{color_code}{value}{reset_code}" if condition else value


def print_header(header: str) -> None:
    """Prints the given header in cyan color with bright styling.

    Args:
        header (str): The header text to be printed.
    Returns:
        None: This function only prints the header with styling and has no return value.
    Example:
        >>> print_header("Important Notice")
        # This will print "Important Notice" in cyan with bright styling.
    """
    print(Fore.CYAN + Style.BRIGHT + header + Style.RESET_ALL)
