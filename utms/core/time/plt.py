from decimal import Decimal
from math import log10

from utms.core.config import constants


def seconds_to_pplt(seconds: Decimal) -> Decimal:
    """Converts seconds to Planck-Centric Planck Log Time (pPLT)."""
    return Decimal(log10(abs(seconds) / constants.PLANCK_TIME_SECONDS))


def seconds_to_hplt(seconds: Decimal) -> Decimal:
    """Converts seconds to Human-Centric Planck Log Time (hPLT)."""
    offset = Decimal(log10(constants.PLANCK_TIME_SECONDS)) + 1
    return Decimal(log10(abs(seconds) / constants.PLANCK_TIME_SECONDS)) + offset
