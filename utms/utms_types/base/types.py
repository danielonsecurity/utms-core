import re
from typing import Any, Optional, TypeAlias, TypeGuard, Union

from .protocols import TimeStamp

# Basic types
IntegerList: TypeAlias = list[int]
OptionalInteger: TypeAlias = Optional[int]
OptionalString: TypeAlias = Optional[str]

# Basic type aliases
TimezoneOffset: TypeAlias = Optional[Union[int, float]]

# Args
ArbitraryArgs: TypeAlias = Any
ArbitraryKwargs: TypeAlias = Any


# Time types
TimeStampList: TypeAlias = list[TimeStamp]
OptionalTimeStampList: TypeAlias = Optional[TimeStampList]

# Files
FilePath: TypeAlias = str


def is_file_path(path: str) -> TypeGuard[FilePath]:
    """Type guard to validate if a string is a valid file path.

    Args:
        path: The string to validate as a file path.

    Returns:
        bool: True if the string is a valid file path, acts as type guard.

    Example:
        >>> if is_file_path(some_string):
        ...     # some_string is now typed as FilePath
        ...     process_path(some_string)
    """
    if not path:
        return False
    if not re.match(r"^[\w$$$$.]+$", path):
        return False
    return True
