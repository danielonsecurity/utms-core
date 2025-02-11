import socket
import sys
from datetime import datetime, timezone
from time import time

import ntplib


def get_ntp_date() -> datetime:
    """Retrieves the current date in datetime format using an NTP (Network Time
    Protocol) server.

    This function queries an NTP server (default is "pool.ntp.org") to
    get the accurate current time. The NTP timestamp is converted to a
    UTC `datetime` object and formatted as a date string. If the NTP
    request fails (due to network issues or other errors), the function
    falls back to the system time.

    Returns:
        str: The current date in 'YYYY-MM-DD' format, either from the
        NTP server or the system clock as a fallback.

    Exceptions:
        - If the NTP request fails, the system time is used instead.
    """
    client = ntplib.NTPClient()
    try:
        # Query the NTP server
        response = client.request("pool.ntp.org", version=3)
        ntp_timestamp = float(response.tx_time)
    except (ntplib.NTPException, socket.error, OSError) as e:
        print(f"Error fetching NTP time: {e}", file=sys.stderr)
        ntp_timestamp = float(time())  # Fallback to system time

    # Convert the timestamp to a UTC datetime and format as 'YYYY-MM-DD'
    current_date = datetime.fromtimestamp(ntp_timestamp, timezone.utc)
    return current_date
