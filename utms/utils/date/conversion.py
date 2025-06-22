from datetime import datetime


def get_seconds_since_midnight() -> int:
    """Get the number of seconds that have passed since midnight today."""
    now = datetime.now(datetime.now().astimezone().tzinfo)  # Get the current local time
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    seconds_since_midnight = (now - midnight).seconds
    return seconds_since_midnight
