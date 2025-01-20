def calculate_decimal_time(seconds: int) -> tuple[int, int, int, float]:
    """Calculate deciday, centiday, decimal seconds, and decidays as a
    float."""
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


def convert_time(input_time: str) -> str:
    """Converts time between 24-hour format (HH:MM:SS or HH:MM) and decimal
    format (DD.CD.SSS or DD.CD).

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
    """Converts 24-hour format (HH:MM:SS or HH:MM) to decimal format (DD.CD.SSS
    or DD.CD).

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
    """Converts decimal format (DD.CD.SSS or DD.CD) to 24-hour format (HH:MM:SS
    or HH:MM).

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
