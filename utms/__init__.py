"""This package provides functionality for a universal time tracking system,
able to measure time from the big bang, until the heat death of the universe,
using meaningful decimal units based on seconds. It can be used to measure the
time between any random events by getting the date from Gemini AI, convert
between various time systems, and more....

Author: [Daniel Neagaru]
"""

from .core import constants
from .core.ai import AI
from .core.anchors import Anchor, AnchorConfig, AnchorManager
from .core.config import Config
from .core.constants import VERSION
