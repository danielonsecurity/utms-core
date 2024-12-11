"""
This package provides functionality for a universal time tracking
system, able to measure time from the big bang, until the heat death
of the universe, using meaningful decimal units based on seconds.
It can be used to measure the time between any random events by
getting the date from Gemini AI, convert between various time systems,
and more....


Author: [Daniel Neagaru]
"""

from .ai import ai_generate_date
from .constants import VERSION

# from .utils import *  # Import utility functions


__all__ = ["ai_generate_date", "VERSION"]
