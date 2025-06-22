from decimal import Decimal
from typing import TYPE_CHECKING, Optional, Protocol, Union

if TYPE_CHECKING:
    from utms.core.time.decimal import DecimalTimeLength, DecimalTimeStamp


class TimeStamp(Protocol):
    """Protocol defining the interface for timestamp values."""

    def copy(self) -> "DecimalTimeStamp": ...

    def __float__(self) -> float: ...

    def __int__(self) -> int: ...

    def __add__(
        self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]
    ) -> "DecimalTimeStamp": ...

    def __radd__(
        self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]
    ) -> "DecimalTimeStamp": ...

    def __iadd__(
        self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]
    ) -> "DecimalTimeStamp": ...  # +=

    def __sub__(
        self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]
    ) -> "DecimalTimeStamp": ...

    def __rsub__(
        self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]
    ) -> "DecimalTimeStamp": ...

    def __isub__(
        self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]
    ) -> "DecimalTimeStamp": ...  # -=

    def __mul__(
        self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]
    ) -> "DecimalTimeLength": ...

    def __rmul__(self, other: Union["TimeLength", int, float, Decimal]) -> "DecimalTimeLength": ...

    def __imul__(
        self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]
    ) -> "DecimalTimeLength": ...  # *=

    def __truediv__(
        self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]
    ) -> "DecimalTimeLength": ...

    def __itruediv__(
        self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]
    ) -> "DecimalTimeLength": ...  # /=

    def __rtruediv__(
        self, other: Union["TimeLength", "TimeLength", int, float, Decimal]
    ) -> "DecimalTimeLength": ...

    def __floordiv__(self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]) -> int: ...

    def __rfloordiv__(
        self, other: Union["TimeLength", "TimeLength", int, float, Decimal]
    ) -> int: ...

    def __ifloordiv__(
        self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]
    ) -> int: ...  # //=

    def __mod__(self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]) -> int: ...

    def __rmod__(self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]) -> int: ...

    def __imod__(
        self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]
    ) -> int: ...  # %=

    def __lt__(self, other: Union["TimeStamp", int, float, Decimal]) -> bool: ...
    def __le__(self, other: Union["TimeStamp", int, float, Decimal]) -> bool: ...
    def __gt__(self, other: Union["TimeStamp", int, float, Decimal]) -> bool: ...
    def __ge__(self, other: Union["TimeStamp", int, float, Decimal]) -> bool: ...
    def __eq__(self, other: object) -> bool: ...

    # Unary operations
    def __neg__(self) -> "DecimalTimeStamp": ...  # -x
    def __pos__(self) -> "DecimalTimeStamp": ...  # +x
    def __abs__(self) -> "DecimalTimeStamp": ...  # abs(x)
    def __round__(self, ndigits: Optional[int] = None) -> "DecimalTimeStamp": ...  # round(x)


class TimeLength(Protocol):
    """Protocol defining the interface for time duration/length values."""

    _seconds: Decimal

    def copy(self) -> "TimeLength": ...

    def __float__(self) -> float: ...
    def __int__(self) -> int: ...

    # Arithmetic with other TimeLengths
    def __add__(
        self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]
    ) -> Union["DecimalTimeLength", "DecimalTimeStamp"]: ...
    def __radd__(
        self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]
    ) -> Union["DecimalTimeLength", "DecimalTimeStamp"]: ...
    def __iadd__(
        self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]
    ) -> Union["DecimalTimeLength", "DecimalTimeStamp"]: ...

    def __sub__(
        self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]
    ) -> Union["DecimalTimeLength", "DecimalTimeStamp"]: ...
    def __rsub__(
        self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]
    ) -> Union["DecimalTimeLength", "DecimalTimeStamp"]: ...
    def __isub__(
        self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]
    ) -> Union["DecimalTimeLength", "DecimalTimeStamp"]: ...

    def __mul__(
        self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]
    ) -> "DecimalTimeLength": ...
    def __rmul__(
        self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]
    ) -> "DecimalTimeLength": ...
    def __imul__(
        self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]
    ) -> "DecimalTimeLength": ...

    def __truediv__(
        self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]
    ) -> "DecimalTimeLength": ...
    def __rtruediv__(
        self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]
    ) -> "DecimalTimeLength": ...
    def __itruediv__(
        self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]
    ) -> "DecimalTimeLength": ...

    def __floordiv__(self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]) -> int: ...
    def __ifloordiv__(
        self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]
    ) -> int: ...
    def __rfloordiv__(
        self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]
    ) -> int: ...

    def __mod__(self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]) -> int: ...
    def __imod__(self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]) -> int: ...
    def __rmod__(self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]) -> int: ...

    # Unary operations
    def __neg__(self) -> "DecimalTimeLength": ...
    def __pos__(self) -> "DecimalTimeLength": ...
    def __abs__(self) -> "DecimalTimeLength": ...
    def __round__(self, ndigits: Optional[int] = None) -> "DecimalTimeLength": ...

    # Comparison
    def __lt__(self, other: Union["TimeLength", int, float, Decimal]) -> bool: ...
    def __le__(self, other: Union["TimeLength", int, float, Decimal]) -> bool: ...
    def __gt__(self, other: Union["TimeLength", int, float, Decimal]) -> bool: ...
    def __ge__(self, other: Union["TimeLength", int, float, Decimal]) -> bool: ...
    def __eq__(self, other: object) -> bool: ...


class TimeRange(Protocol):
    """Protocol for time range"""

    @property
    def start(self) -> "TimeStamp": ...

    @property
    def duration(self) -> "TimeLength": ...

    @property
    def end(self) -> "TimeStamp": ...

    def contains(self, timestamp: "TimeStamp") -> bool: ...
    def overlaps(self, other: "TimeRange") -> bool: ...
