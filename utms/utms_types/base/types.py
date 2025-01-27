from typing import TypeAlias, Optional, Union, Any
from .protocols import TimeStamp

# Basic types
IntegerList: TypeAlias = list[int]
OptionalInteger: TypeAlias = Optional[int]

# Basic type aliases
TimezoneOffset: TypeAlias = Optional[Union[int, float]]

# Args
ArbitraryArgs: TypeAlias = Any
ArbitraryKwargs: TypeAlias = Any


# Time types
TimeStampList: TypeAlias = list[TimeStamp]
OptionalTimeStampList: TypeAlias = Optional[TimeStampList]

