"""
This module defines the `Config` class, which manages the configuration of time units and datetime
anchors.

The `Config` class is responsible for populating predefined time units and datetime anchors.  It
uses the `UnitManager` class to manage time units such as Planck Time, Picoseconds, and
Milliseconds, and the `AnchorManager` class to manage datetime anchors like Unix Time, CE Time, and
Big Bang Time.

Constants from the `constants` module are used to define the values for the time units and anchors.

Modules:
- `utms.constants`: Contains predefined constants for time and datetime values.
- `utms.anchors`: Contains the `AnchorManager` class for managing datetime anchors.
- `utms.units`: Contains the `UnitManager` class for managing time units.

Usage:
- Instantiate the `Config` class to initialize the units and anchors with predefined values.
"""

import socket
from datetime import datetime, timezone
from decimal import Decimal
from time import time

import ntplib

from utms import constants
from utms.anchors import AnchorManager
from utms.units import UnitManager


def get_ntp_date() -> datetime:
    """
    Retrieves the current date in datetime format using an NTP (Network Time Protocol) server.

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
    except (ntplib.NTPException, socket.error, OSError) as e:  # pragma: no cover
        print(f"Error fetching NTP time: {e}")
        ntp_timestamp = float(time())  # Fallback to system time

    # Convert the timestamp to a UTC datetime and format as 'YYYY-MM-DD'
    current_date = datetime.fromtimestamp(ntp_timestamp, timezone.utc)
    return current_date


class Config:
    """
    Configuration class that manages units and anchors for time and datetime references.

    This class is responsible for populating time units and datetime anchors based on predefined
    constants.  It uses the `AnchorManager` and `UnitManager` classes to add relevant time units and
    datetime anchors.
    """

    def __init__(self) -> None:
        """
        Initializes the configuration by creating instances of `AnchorManager` and `UnitManager`,
        then populating them with units and anchors.

        This method calls `populate_units()` to add time units and `populate_anchors()` to add
        datetime anchors.
        """
        self.units = UnitManager()
        self.anchors = AnchorManager(self.units)
        self.populate_units()
        self.populate_anchors()

    def populate_units(self) -> None:
        """
        Populates the `UnitManager` instance with predefined time units.

        This method adds time units ranging from Planck Time to Milliseconds using the
        `add_time_unit` method of the `UnitManager` instance. Each unit is added with its name,
        symbol, and corresponding time in seconds.
        """
        # Add time units
        self.units.add_time_unit("Planck Time", "pt", constants.PLANCK_TIME_SECONDS)

        self.units.add_time_unit("Quectosecond", "qs", Decimal("1e-30"))
        self.units.add_time_unit("Rontosecond", "rs", Decimal("1e-27"))
        self.units.add_time_unit("Yoctosecond", "ys", Decimal("1e-24"))
        self.units.add_time_unit("Zeptosecond", "zs", Decimal("1e-21"))
        self.units.add_time_unit("Attosecond", "as", Decimal("1e-18"))
        self.units.add_time_unit("Femtosecond", "fs", Decimal("1e-15"))
        self.units.add_time_unit("Picosecond", "ps", Decimal("1e-12"))
        self.units.add_time_unit("Nanosecond", "ns", Decimal("1e-9"))
        self.units.add_time_unit("Microsecond", "us", Decimal("1e-6"))
        self.units.add_time_unit("Millisecond", "ms", Decimal("1e-3"))

        self.units.add_time_unit("Second", "s", Decimal(1))

        self.units.add_time_unit("Kilosecond", "KS", Decimal("1e3"))
        self.units.add_time_unit("Megasecond", "MS", Decimal("1e6"))
        self.units.add_time_unit("Gigasecond", "GS", Decimal("1e9"))
        self.units.add_time_unit("Terasecond", "TS", Decimal("1e12"))
        self.units.add_time_unit("Petasecond", "PS", Decimal("1e15"))
        self.units.add_time_unit("Exasecond", "ES", Decimal("1e18"))
        self.units.add_time_unit("Zettasecond", "ZS", Decimal("1e21"))
        self.units.add_time_unit("Yottasecond", "YS", Decimal("1e24"))
        self.units.add_time_unit("Ronnasecond", "RS", Decimal("1e27"))
        self.units.add_time_unit("Quettasecond", "QS", Decimal("1e30"))

        self.units.add_time_unit("Minute", "m", constants.SECONDS_IN_MINUTE)
        self.units.add_time_unit("Hour", "h", constants.SECONDS_IN_HOUR)
        self.units.add_time_unit("Day", "d", constants.SECONDS_IN_DAY)
        self.units.add_time_unit("Week", "w", constants.SECONDS_IN_WEEK)
        self.units.add_time_unit("Month", "M", constants.SECONDS_IN_MONTH)
        self.units.add_time_unit("Quarter", "Q", constants.SECONDS_IN_YEAR / 4)
        self.units.add_time_unit("Year", "Y", constants.SECONDS_IN_YEAR)
        self.units.add_time_unit("Decade", "D", constants.SECONDS_IN_YEAR * 10)
        self.units.add_time_unit("Century", "C", constants.SECONDS_IN_YEAR * 100)
        self.units.add_time_unit("Millennium", "Mn", constants.SECONDS_IN_YEAR * 1000)

        self.units.add_time_unit("Deciday", "dd", constants.SECONDS_IN_DAY / 10)
        self.units.add_time_unit("Centiday", "cd", constants.SECONDS_IN_DAY / 100)

        self.units.add_time_unit("Lunar Cycle", "lc", constants.SECONDS_IN_LUNAR_CYCLE)

        self.units.add_time_unit("Megaannum", "Ma", constants.SECONDS_IN_YEAR * Decimal(1e6))
        self.units.add_time_unit("Gigaannum", "Ga", constants.SECONDS_IN_YEAR * Decimal(1e9))
        self.units.add_time_unit("Teraannum", "Ta", constants.SECONDS_IN_YEAR * Decimal(1e12))

        self.units.add_time_unit("Age of Universe", "au", constants.AGE_OF_UNIVERSE_SECONDS)
        self.units.add_time_unit("Hubble Time", "ht", constants.HUBBLE_TIME_SECONDS)
        self.units.add_time_unit("Galaxial Era", "GE", constants.GALAXIAL_ERA)

    def populate_anchors(self) -> None:
        """
        Populates the `AnchorManager` instance with predefined datetime anchors.

        This method adds various datetime anchors such as Unix Time, CE Time, and Big Bang Time,
        using the `add_datetime_anchor` and `add_decimal_anchor` methods of the `AnchorManager`
        instance.  Each anchor is added with its name, symbol, and corresponding datetime value.
        """
        self.anchors.add_anchor(
            f"Now Time ({datetime.now().strftime('%Y-%m-%d')})", "NT", get_ntp_date()
        )
        self.anchors.add_anchor(
            f"Day Time ({datetime.now().strftime('%Y-%m-%d 00:00:00')})",
            "DT",
            datetime(
                datetime.now().year,
                datetime.now().month,
                datetime.now().day,
                tzinfo=datetime.now().astimezone().tzinfo,
            ),
            precision=Decimal(1e-6),
            breakdowns=[["dd", "cd", "s", "ms"], ["h", "m", "s", "ms"], ["KS", "s", "ms"]],
        )
        self.anchors.add_anchor(
            f"Year Time ({datetime.now().strftime('%Y-01-01 00:00:00')})",
            "YT",
            datetime(
                datetime.now().year,
                1,
                1,
                tzinfo=datetime.now().astimezone().tzinfo,
            ),
            precision=Decimal(1e-6),
            breakdowns=[
                ["d", "dd", "cd", "s", "ms"],
                ["w", "d", "dd", "cd", "s", "ms"],
                ["M", "d", "dd", "cd", "s", "ms"],
                ["MS", "KS", "s", "ms"],
            ],
        )
        self.anchors.add_anchor(
            f"Month Time ({datetime.now().strftime('%Y-%m-01 00:00:00')})",
            "MT",
            datetime(
                datetime.now().year,
                datetime.now().month,
                1,
                tzinfo=datetime.now().astimezone().tzinfo,
            ),
            precision=Decimal(1e-6),
            breakdowns=[
                ["d", "dd", "cd", "s", "ms"],
                ["w", "d", "dd", "cd", "s", "ms"],
                ["MS", "KS", "s", "ms"],
            ],
        )
        self.anchors.add_anchor(
            "Unix Time (1970-01-01)",
            "UT",
            constants.UNIX_DATE,
            breakdowns=[
                ["s"],
                ["PS", "TS", "GS", "MS", "KS", "s"],
                ["Ga", "Ma", "Mn", "Y", "d", "h", "m", "s"],
                ["Y"],
            ],
        )
        self.anchors.add_anchor("CE Time (1 CE)", "CE", constants.CE_DATE)
        self.anchors.add_anchor("Millennium Time (2000-01-01)", "mT", constants.MILLENNIUM_DATE)
        self.anchors.add_anchor("Life Time (1992-27-06)", "LT", constants.LIFE_DATE)
        self.anchors.add_anchor(
            "Big Bang Time (13.8e9 years ago)",
            "BB",
            -constants.AGE_OF_UNIVERSE_SECONDS,
            precision=Decimal(1e6),
            breakdowns=[["Y"], ["Ga", "Ma"], ["TS", "GS", "MS", "KS", "s", "ms"]],
        )
