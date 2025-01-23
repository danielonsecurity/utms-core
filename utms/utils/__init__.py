# utms/utils/__init__.py
from typing import List, Set

from . import date, display, logger, time
from .date import *
from .display import *
from .logger import *
from .time import *


def combine_all_lists(*modules: List[str]) -> List[str]:
    """Combine multiple __all__ lists into one, removing duplicates."""
    all_names: Set[str] = set()
    for module in modules:
        all_names.update(module)
    return sorted(list(all_names))


__all__ = combine_all_lists(display.__all__, time.__all__, date.__all__)
