"""
Time Unit Management and Physical Constants Module

This module provides utilities for handling time units, converting between them, and
managing high-precision physical constants related to time and the universe. It uses
`Decimal` for high-precision arithmetic and allows the user to define, add, and convert
between various time units ranging from Planck time to multi-million-year scales.

Modules:
    math: For mathematical constants and functions.
    datetime: For date and time handling.
    decimal: For high-precision decimal arithmetic.
    importlib.metadata: For fetching package version information.
    utms.units: For managing time units through the `TimeUnitManager`.

Constants:
    - HBAR: Reduced Planck constant in Joule-seconds (J⋅s).
    - G_CONST: Gravitational constant in m^3⋅kg^−1⋅s^−2.
    - C_CONST: Speed of light in meters per second (m/s).
    - PLANCK_TIME_SECONDS: Planck time in seconds, a fundamental time scale in physics.
    - SECONDS_IN_*: Constants representing the number of seconds in various time
      periods, such as minutes, hours, days, weeks, months, years, etc.
    - AGE_OF_UNIVERSE_YEARS: The age of the universe in years.
    - UNIVERSE_MAX_LIFESPAN_YEARS: Estimated lifespan of the universe in years.
    - GALAXIAL_ERA: The estimated maximum lifespan of the universe in seconds.
    - PLANCK_TIME_EPOCH: Epoch time of Planck time, derived from the maximum lifespan
      of the universe.

Time Units:
    - The module includes definitions for common human time units like second, minute,
      hour, day, etc., as well as exotic time units such as Planck time, and units
      spanning multiple scales, including megaannum and galactical eras.

    - A dictionary `TIME_UNITS` maps each time unit name to its corresponding time in
      seconds, and `HUMAN_TIME_UNITS` offers more familiar human units.

Functions:
    - TimeUnitManager instance to manage and convert between these units.
    - The manager is used to add custom time units, such as "Lunar cycle", "Hubble time",
      and others, to provide a comprehensive set of time units for conversions and
      calculations.

Version:
    - The module version is determined from the installed `utms` package, or set to
      "0.0.0" if the package is not found.

Precision:
    - The `Decimal` module is used for all constants and calculations to ensure high
      precision (up to 200 decimal places), avoiding floating-point errors, especially
      in scientific computations.
"""

import math
from datetime import datetime, timezone
from decimal import Decimal, getcontext
from importlib.metadata import PackageNotFoundError, version

from utms.units import TimeUnitManager

try:
    VERSION = version("utms")
except PackageNotFoundError:  # pragma: no cover
    VERSION = "0.0.0"

# Set precision for Decimal calculations
getcontext().prec = 200

# Constants with high precision
HBAR = Decimal("1.054571817e-34")  # Reduced Planck constant in J⋅s
G_CONST = Decimal("6.67430e-11")  # Gravitational constant in m^3⋅kg^−1⋅s^−2
C_CONST = Decimal("299792458")  # Speed of light in m/s

# Planck time calculation
PLANCK_TIME_SECONDS = Decimal(math.sqrt((HBAR * G_CONST) / (C_CONST**5)))


# Human time units in Decimal
SECONDS_IN_MINUTE = Decimal(60)
SECONDS_IN_HOUR = SECONDS_IN_MINUTE * Decimal(60)
SECONDS_IN_DAY = SECONDS_IN_HOUR * Decimal(24)
SECONDS_IN_WEEK = SECONDS_IN_DAY * Decimal(7)
SECONDS_IN_MONTH = SECONDS_IN_DAY * Decimal(30)  # Approximation
SECONDS_IN_YEAR = SECONDS_IN_DAY * Decimal(365.25)
SECONDS_IN_CENTURY = SECONDS_IN_YEAR * Decimal(100)
SECONDS_IN_MILLENNIUM = SECONDS_IN_YEAR * Decimal(1000)

# Seconds in lunar cycle
SECONDS_IN_LUNAR_CYCLE = (
    SECONDS_IN_DAY * 29 + SECONDS_IN_HOUR * 12 + SECONDS_IN_MINUTE * 44 + Decimal(2.8)
)


# Constants for universe age calculation
AGE_OF_UNIVERSE_YEARS = Decimal("13.8e9")  # Age of the universe in years
AGE_OF_UNIVERSE_SECONDS = AGE_OF_UNIVERSE_YEARS * SECONDS_IN_YEAR

# Constants for Hubble Time
HUBBLE_TIME_YEARS = Decimal("14.4e9")  # Age of the universe in years
HUBBLE_TIME_SECONDS = HUBBLE_TIME_YEARS * SECONDS_IN_YEAR

# Maximum length of the universe lifespan from the Big Bang until the heat
# death of the universe
UNIVERSE_MAX_LIFESPAN_YEARS = Decimal("1e120")
GALAXIAL_ERA = UNIVERSE_MAX_LIFESPAN_YEARS * SECONDS_IN_YEAR

# Planck Time Epoch (PTE)
PLANCK_TIME_EPOCH = GALAXIAL_ERA / PLANCK_TIME_SECONDS

MILLENNIUM_DATE = datetime(2000, 1, 1, 0, 0, tzinfo=timezone.utc)
CE_DATE = datetime(1, 1, 1, 0, 0, tzinfo=timezone.utc)
LIFE_DATE = datetime(1992, 6, 27, 0, 0, tzinfo=timezone.utc)
UNIX_DATE = datetime(1970, 1, 1, 0, 0, tzinfo=timezone.utc)


# Create a TimeUnitManager instance
manager = TimeUnitManager()

# Add time units
manager.add_time_unit("Planck Time", "pt", PLANCK_TIME_SECONDS)

manager.add_time_unit("Quectosecond", "qs", Decimal("1e-30"))
manager.add_time_unit("Rontosecond", "rs", Decimal("1e-27"))
manager.add_time_unit("Yoctosecond", "ys", Decimal("1e-24"))
manager.add_time_unit("Zeptosecond", "zs", Decimal("1e-21"))
manager.add_time_unit("Attosecond", "as", Decimal("1e-18"))
manager.add_time_unit("Femtosecond", "fs", Decimal("1e-15"))
manager.add_time_unit("Picosecond", "ps", Decimal("1e-12"))
manager.add_time_unit("Nanosecond", "ns", Decimal("1e-9"))
manager.add_time_unit("Microsecond", "us", Decimal("1e-6"))
manager.add_time_unit("Millisecond", "ms", Decimal("1e-3"))

manager.add_time_unit("Second", "s", Decimal(1))

manager.add_time_unit("Kilosecond", "KS", Decimal("1e3"))
manager.add_time_unit("Megasecond", "MS", Decimal("1e6"))
manager.add_time_unit("Gigasecond", "GS", Decimal("1e9"))
manager.add_time_unit("Terasecond", "TS", Decimal("1e12"))
manager.add_time_unit("Petasecond", "PS", Decimal("1e15"))
manager.add_time_unit("Exasecond", "ES", Decimal("1e18"))
manager.add_time_unit("Zettasecond", "ZS", Decimal("1e21"))
manager.add_time_unit("Yottasecond", "YS", Decimal("1e24"))
manager.add_time_unit("Ronnasecond", "RS", Decimal("1e24"))
manager.add_time_unit("Quettasecond", "QS", Decimal("1e24"))

manager.add_time_unit("Minute", "m", SECONDS_IN_MINUTE)
manager.add_time_unit("Hour", "h", SECONDS_IN_HOUR)
manager.add_time_unit("Day", "d", SECONDS_IN_DAY)
manager.add_time_unit("Week", "w", SECONDS_IN_WEEK)
manager.add_time_unit("Month", "M", SECONDS_IN_MONTH)
manager.add_time_unit("Year", "Y", SECONDS_IN_YEAR)
manager.add_time_unit("Decade", "D", SECONDS_IN_YEAR * 10)
manager.add_time_unit("Century", "C", SECONDS_IN_YEAR * 100)
manager.add_time_unit("Millennium", "Mn", SECONDS_IN_YEAR * 1000)

manager.add_time_unit("Lunar Cycle", "lc", SECONDS_IN_LUNAR_CYCLE)

manager.add_time_unit("Megaannum", "Ma", SECONDS_IN_YEAR * Decimal(1e6))
manager.add_time_unit("Gigaannum", "Ga", SECONDS_IN_YEAR * Decimal(1e9))
manager.add_time_unit("Teraannum", "Ta", SECONDS_IN_YEAR * Decimal(1e12))

manager.add_time_unit("Age of Universe", "au", AGE_OF_UNIVERSE_SECONDS)
manager.add_time_unit("Hubble Time", "ht", HUBBLE_TIME_SECONDS)
manager.add_time_unit("Galaxial Era", "GE", GALAXIAL_ERA)
