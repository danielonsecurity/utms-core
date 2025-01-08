"""
This package provides functionality for a universal time tracking
system, able to measure time from the big bang, until the heat death
of the universe, using meaningful decimal units based on seconds.
It can be used to measure the time between any random events by
getting the date from Gemini AI, convert between various time systems,
and more....


Author: [Daniel Neagaru]
"""

from .ai import AI
from .config import Config
from .constants import VERSION

__all__ = ["AI", "Config", "VERSION"]
