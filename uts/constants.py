"""
Here are stored constants needed by the package.
"""

import math
from datetime import datetime, timezone
from decimal import Decimal, getcontext
from importlib.metadata import PackageNotFoundError, version

try:
    VERSION = version("uts")
except PackageNotFoundError:
    VERSION = "0.0.0"

    # Set precision for Decimal calculations
getcontext().prec = 110

# Constants with high precision
HBAR = Decimal("1.054571817e-34")  # Reduced Planck constant in J⋅s
G_CONST = Decimal("6.67430e-11")  # Gravitational constant in m^3⋅kg^−1⋅s^−2
C_CONST = Decimal("299792458")  # Speed of light in m/s

# Planck time calculation
PLANCK_TIME_SECONDS = Decimal(math.sqrt((HBAR * G_CONST) / (C_CONST**5)))

# Constants for universe age calculation
AGE_OF_UNIVERSE_YEARS = Decimal("13.8e9")  # Age of the universe in years

# Human time units in Decimal
SECONDS_IN_MINUTE = Decimal(60)
SECONDS_IN_HOUR = SECONDS_IN_MINUTE * Decimal(60)
SECONDS_IN_DAY = SECONDS_IN_HOUR * Decimal(24)
SECONDS_IN_WEEK = SECONDS_IN_DAY * Decimal(7)
SECONDS_IN_MONTH = SECONDS_IN_DAY * Decimal(30)  # Approximation
SECONDS_IN_YEAR = SECONDS_IN_DAY * Decimal(365.25)
SECONDS_IN_CENTURY = SECONDS_IN_YEAR * Decimal(100)
SECONDS_IN_MILLENNIUM = SECONDS_IN_YEAR * Decimal(1000)

# Time units in seconds for conversion
TIME_UNITS = {
    "Kilosecond (KSec)": Decimal("1e3"),
    "Megasecond (MSec)": Decimal("1e6"),
    "Gigasecond (GSec)": Decimal("1e9"),
    "Terasecond (TSec)": Decimal("1e12"),
    "Petasecond (PSec)": Decimal("1e15"),
}


HUMAN_TIME_UNITS = {
    "1 Second": Decimal(1),
    "1 Minute": SECONDS_IN_MINUTE,
    "1 Hour": SECONDS_IN_HOUR,
    "1 Day": SECONDS_IN_DAY,
    "1 Week": SECONDS_IN_WEEK,
    "1 Month": SECONDS_IN_MONTH,
    "1 Year": SECONDS_IN_YEAR,
    "1 Century": SECONDS_IN_CENTURY,
    "1 Millennium": SECONDS_IN_MILLENNIUM,
}


MILLENNIUM_DATE = datetime(2000, 1, 1, 0, 0, tzinfo=timezone.utc)
CE_DATE = datetime(1, 1, 1, 0, 0, tzinfo=timezone.utc)
LIFE_DATE = datetime(1992, 6, 27, 0, 0, tzinfo=timezone.utc)
