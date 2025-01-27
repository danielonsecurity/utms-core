from decimal import Decimal
from typing import TYPE_CHECKING, Optional, Union

if TYPE_CHECKING:
    from .protocols import TimeLength, TimeStamp


class DecimalTimeStamp:
    """Default implementation of TimeStamp using Decimal for precision."""

    def copy(self) -> "DecimalTimeStamp":
        """Create a new instance with the same value."""
        return DecimalTimeStamp(self._value)

    def __init__(self, value: Union[int, float, Decimal, "DecimalTimeStamp"]) -> None:
        if isinstance(value, DecimalTimeStamp):
            self._value: Decimal = value._value
        else:
            self._value = Decimal(str(value))

    def __float__(self) -> float:
        return float(self._value)

    def __int__(self) -> int:
        return int(self._value)

    def __add__(
        self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]
    ) -> "DecimalTimeStamp":
        if isinstance(other, DecimalTimeStamp):
            return DecimalTimeStamp(self._value + other._value)
        if isinstance(other, DecimalTimeLength):
            return DecimalTimeStamp(self._value + other._seconds)
        return DecimalTimeStamp(self._value + Decimal(str(other)))

    def __radd__(
        self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]
    ) -> "DecimalTimeStamp":
        if isinstance(other, DecimalTimeStamp):
            return DecimalTimeStamp(self._value + other._value)
        elif isinstance(other, DecimalTimeLength):
            return DecimalTimeStamp(other._seconds + self._value)
        return DecimalTimeStamp(Decimal(str(other)) + self._value)

    def __iadd__(
        self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]
    ) -> "DecimalTimeStamp":
        if isinstance(other, DecimalTimeStamp):
            self._value += other._value
        elif isinstance(other, DecimalTimeLength):
            self._value += other._seconds
        else:
            self._value += Decimal(str(other))
        return self

    def __sub__(
        self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]
    ) -> "DecimalTimeStamp":
        if isinstance(other, DecimalTimeStamp):
            return DecimalTimeStamp(self._value - other._value)
        if isinstance(other, DecimalTimeLength):
            return DecimalTimeStamp(self._value - other._seconds)
        return DecimalTimeStamp(self._value - Decimal(str(other)))

    def __rsub__(
        self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]
    ) -> "DecimalTimeStamp":
        if isinstance(other, DecimalTimeStamp):
            return DecimalTimeStamp(other._value - self._value)
        if isinstance(other, DecimalTimeLength):
            return DecimalTimeStamp(other._seconds - self._value)
        return DecimalTimeStamp(Decimal(str(other)) - self._value)

    def __isub__(
        self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]
    ) -> "DecimalTimeStamp":
        if isinstance(other, DecimalTimeStamp):
            self._value -= other._value
        elif isinstance(other, DecimalTimeLength):
            self._value -= other._seconds
        else:
            self._value -= Decimal(str(other))
        return self

    def __truediv__(
        self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]
    ) -> "DecimalTimeLength":
        if isinstance(other, DecimalTimeStamp):
            return DecimalTimeLength(self._value / other._value)
        if isinstance(other, DecimalTimeLength):
            return DecimalTimeLength(self._value / other._seconds)
        return DecimalTimeLength(self._value / Decimal(str(other)))

    def __rtruediv__(
        self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]
    ) -> "DecimalTimeLength":
        if isinstance(other, DecimalTimeStamp):
            return DecimalTimeLength(other._value / self._value)
        if isinstance(other, DecimalTimeLength):
            return DecimalTimeLength(other._seconds / self._value)
        return DecimalTimeLength(Decimal(str(other)) / self._value)

    def __itruediv__(
        self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]
    ) -> "DecimalTimeLength":
        if isinstance(other, DecimalTimeStamp):
            self._value /= other._value
        elif isinstance(other, DecimalTimeLength):
            self._value /= other._seconds
        else:
            self._value /= Decimal(str(other))
        return DecimalTimeLength(self._value)

    def __floordiv__(self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]) -> int:
        if isinstance(other, DecimalTimeStamp):
            return int(self._value // other._value)
        if isinstance(other, DecimalTimeLength):
            return int(self._value // other._seconds)
        return int(self._value // Decimal(str(other)))

    def __rfloordiv__(self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]) -> int:
        if isinstance(other, DecimalTimeStamp):
            return int(other._value // self._value)
        if isinstance(other, DecimalTimeLength):
            return int(other._seconds // self._value)
        return int(Decimal(str(other)) // self._value)

    def __ifloordiv__(self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]) -> int:
        if isinstance(other, DecimalTimeStamp):
            self._value //= other._value
        elif isinstance(other, DecimalTimeLength):
            self._value //= other._seconds
        else:
            self._value //= Decimal(str(other))
        return int(self)

    def __mul__(
        self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]
    ) -> "DecimalTimeLength":
        if isinstance(other, DecimalTimeStamp):
            return DecimalTimeLength(self._value * other._value)
        if isinstance(other, DecimalTimeLength):
            return DecimalTimeLength(self._value * other._seconds)
        return DecimalTimeLength(self._value * Decimal(str(other)))

    def __rmul__(
        self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]
    ) -> "DecimalTimeLength":
        if isinstance(other, DecimalTimeStamp):
            return DecimalTimeLength(other._value * self._value)
        if isinstance(other, DecimalTimeLength):
            return DecimalTimeLength(other._seconds * self._value)
        return DecimalTimeLength(Decimal(str(other)) * self._value)

    def __imul__(
        self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]
    ) -> "DecimalTimeLength":
        if isinstance(other, DecimalTimeStamp):
            self._value *= other._value
        elif isinstance(other, DecimalTimeLength):
            self._value *= other._seconds
        else:
            self._value *= Decimal(str(other))
        return DecimalTimeLength(self._value)

    def __mod__(self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]) -> int:
        if isinstance(other, DecimalTimeStamp):
            return int(self._value % other._value)
        if isinstance(other, DecimalTimeLength):
            return int(self._value % other._seconds)
        return int(self._value % Decimal(str(other)))

    def __rmod__(self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]) -> int:
        if isinstance(other, DecimalTimeStamp):
            return int(other._value % self._value)
        if isinstance(other, DecimalTimeLength):
            return int(other._seconds % self._value)
        return int(Decimal(str(other)) % self._value)

    def __imod__(self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]) -> int:
        if isinstance(other, DecimalTimeStamp):
            self._value %= other._value
        elif isinstance(other, DecimalTimeLength):
            self._value %= other._seconds
        else:
            self._value %= Decimal(str(other))
        return int(self)

    def __lt__(self, other: Union["TimeStamp", int, float, Decimal]) -> bool:
        if isinstance(other, DecimalTimeStamp):
            return self._value < other._value
        return self._value < Decimal(str(other))

    def __le__(self, other: Union["TimeStamp", int, float, Decimal]) -> bool:
        if isinstance(other, DecimalTimeStamp):
            return self._value <= other._value
        return self._value <= Decimal(str(other))

    def __gt__(self, other: Union["TimeStamp", int, float, Decimal]) -> bool:
        if isinstance(other, DecimalTimeStamp):
            return self._value > other._value
        return self._value > Decimal(str(other))

    def __ge__(self, other: Union["TimeStamp", int, float, Decimal]) -> bool:
        if isinstance(other, DecimalTimeStamp):
            return self._value >= other._value
        return self._value >= Decimal(str(other))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, DecimalTimeStamp):
            return self._value == other._value
        if isinstance(other, (int, float, Decimal)):
            return self._value == Decimal(str(other))
        return NotImplemented

    def __neg__(self) -> "DecimalTimeStamp":
        return DecimalTimeStamp(-self._value)

    def __pos__(self) -> "DecimalTimeStamp":
        return DecimalTimeStamp(+self._value)

    def __abs__(self) -> "DecimalTimeStamp":
        return DecimalTimeStamp(abs(self._value))

    def __round__(self, ndigits: Optional[int] = None) -> "DecimalTimeStamp":
        return DecimalTimeStamp(
            round(self._value, ndigits) if ndigits is not None else round(self._value)
        )

    def __str__(self) -> str:
        return str(self._value)

    def __repr__(self) -> str:
        return f"DecimalTimeStamp({self._value})"


class DecimalTimeLength:
    """Implementation of TimeLength using Decimal for precision."""

    def __init__(self, seconds: Union[int, float, Decimal, "DecimalTimeLength"]) -> None:
        self._seconds: Decimal
        if isinstance(seconds, DecimalTimeLength):
            self._seconds = seconds._seconds
        else:
            self._seconds = Decimal(str(seconds))

    def copy(self) -> "DecimalTimeLength":
        """Create a new instance with the same value."""
        return DecimalTimeLength(self._seconds)

    def __float__(self) -> float:
        return float(self._seconds)

    def __int__(self) -> int:
        return int(self._seconds)

    # Basic arithmetic operations
    def __add__(
        self, other: Union["TimeLength", "TimeStamp", int, float, Decimal]
    ) -> Union[DecimalTimeStamp, "DecimalTimeLength"]:
        if isinstance(other, DecimalTimeLength):
            return DecimalTimeLength(self._seconds + other._seconds)
        elif isinstance(other, DecimalTimeStamp):
            return DecimalTimeStamp(self._seconds + other._value)
        return DecimalTimeLength(self._seconds + Decimal(str(other)))

    def __radd__(
        self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]
    ) -> Union["DecimalTimeStamp", "DecimalTimeLength"]:
        if isinstance(other, DecimalTimeLength):
            return DecimalTimeLength(other._seconds + self._seconds)
        elif isinstance(other, DecimalTimeStamp):
            return DecimalTimeStamp(other._value + self._seconds)
        return DecimalTimeLength(Decimal(str(other)) + self._seconds)

    def __iadd__(
        self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]
    ) -> Union["DecimalTimeStamp", "DecimalTimeLength"]:
        if isinstance(other, DecimalTimeLength):
            self._seconds += other._seconds
        elif isinstance(other, DecimalTimeStamp):
            self._seconds += other._value
            return DecimalTimeStamp(self._seconds)
        else:
            self._seconds += Decimal(str(other))
        return self

    def __sub__(
        self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]
    ) -> Union["DecimalTimeLength", DecimalTimeStamp]:
        if isinstance(other, DecimalTimeLength):
            return DecimalTimeLength(self._seconds - other._seconds)
        elif isinstance(other, DecimalTimeStamp):
            return DecimalTimeStamp(self._seconds - other._value)
        return DecimalTimeLength(self._seconds - Decimal(str(other)))

    def __rsub__(
        self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]
    ) -> Union["DecimalTimeStamp", "DecimalTimeLength"]:
        return DecimalTimeLength(Decimal(str(other)) - self._seconds)

    def __isub__(
        self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]
    ) -> Union["DecimalTimeStamp", "DecimalTimeLength"]:
        if isinstance(other, DecimalTimeLength):
            self._seconds -= other._seconds
        elif isinstance(other, DecimalTimeStamp):
            self._seconds -= other._value
            return DecimalTimeStamp(self._seconds)
        else:
            self._seconds -= Decimal(str(other))
        return self

    def __mul__(
        self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]
    ) -> "DecimalTimeLength":
        return DecimalTimeLength(self._seconds * Decimal(str(other)))

    def __rmul__(
        self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]
    ) -> "DecimalTimeLength":
        return DecimalTimeLength(Decimal(str(other)) * self._seconds)

    def __imul__(
        self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]
    ) -> "DecimalTimeLength":
        self._seconds *= Decimal(str(other))
        return self

    def __truediv__(
        self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]
    ) -> "DecimalTimeLength":
        if isinstance(other, DecimalTimeLength):
            return DecimalTimeLength(
                self._seconds / other._seconds
            )  # Returns ratio between lengths
        return DecimalTimeLength(self._seconds / Decimal(str(other)))

    def __rtruediv__(
        self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]
    ) -> "DecimalTimeLength":
        return DecimalTimeLength(Decimal(str(other)) / self._seconds)

    def __itruediv__(
        self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]
    ) -> "DecimalTimeLength":
        self._seconds /= Decimal(str(other))
        return self

    def __floordiv__(self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]) -> int:
        if isinstance(other, DecimalTimeLength):
            return int(self._seconds // other._seconds)
        return int(self._seconds // Decimal(str(other)))

    def __rfloordiv__(self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]) -> int:
        return int(Decimal(str(other)) // self._seconds)

    def __ifloordiv__(self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]) -> int:
        self._seconds //= Decimal(str(other))
        return int(self)

    def __mod__(self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]) -> int:
        if isinstance(other, DecimalTimeLength):
            return int(self._seconds % other._seconds)
        return int(self._seconds % Decimal(str(other)))

    def __rmod__(self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]) -> int:
        return int(Decimal(str(other)) % self._seconds)

    def __imod__(self, other: Union["TimeStamp", "TimeLength", int, float, Decimal]) -> int:
        self._seconds %= Decimal(str(other))
        return int(self)

    # Unary operations
    def __neg__(self) -> "DecimalTimeLength":
        return DecimalTimeLength(-self._seconds)

    def __pos__(self) -> "DecimalTimeLength":
        return DecimalTimeLength(+self._seconds)

    def __abs__(self) -> "DecimalTimeLength":
        return DecimalTimeLength(abs(self._seconds))

    def __round__(self, ndigits: Optional[int] = None) -> "DecimalTimeLength":
        return DecimalTimeLength(
            round(self._seconds, ndigits) if ndigits is not None else round(self._seconds)
        )

    # Comparison operations
    def __lt__(self, other: Union["TimeLength", int, float, Decimal]) -> bool:
        if isinstance(other, DecimalTimeLength):
            return bool(self._seconds < other._seconds)
        return bool(self._seconds < Decimal(str(other)))

    def __le__(self, other: Union["TimeLength", int, float, Decimal]) -> bool:
        if isinstance(other, DecimalTimeLength):
            return bool(self._seconds <= other._seconds)
        return bool(self._seconds <= Decimal(str(other)))

    def __gt__(self, other: Union["TimeLength", int, float, Decimal]) -> bool:
        if isinstance(other, DecimalTimeLength):
            return bool(self._seconds > other._seconds)
        return bool(self._seconds > Decimal(str(other)))

    def __ge__(self, other: Union["TimeLength", int, float, Decimal]) -> bool:
        if isinstance(other, DecimalTimeLength):
            return bool(self._seconds >= other._seconds)
        return bool(self._seconds >= Decimal(str(other)))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, DecimalTimeLength):
            return bool(self._seconds == other._seconds)
        if isinstance(other, (int, float, Decimal)):
            return bool(self._seconds == Decimal(str(other)))
        return NotImplemented

    def __str__(self) -> str:
        return f"{self._seconds}"

    def __repr__(self) -> str:
        return f"DecimalTimeLength({self._seconds})"


class TimeRange:
    """Represents a time range with start and end timestamps."""

    def __init__(self, start: "TimeStamp", end: "TimeStamp") -> None:
        self.start: "TimeStamp" = start
        self.end: "TimeStamp" = end

    def __post_init__(self) -> None:
        """Validate that end is not before start."""
        if self.end < self.start:
            raise ValueError("TimeRange end cannot be before start")

    @property
    def duration(self) -> "TimeStamp":
        """Calculate the duration of the time range."""
        return self.end - self.start

    def contains(self, timestamp: "TimeStamp") -> bool:
        """Check if a timestamp falls within this range."""
        return self.start <= timestamp < self.end

    def overlaps(self, other: "TimeRange") -> bool:
        """Check if this range overlaps with another range."""
        return self.start < other.end and self.end > other.start

    def __str__(self) -> str:
        """String representation of TimeRange.

        Format: [start -> end] (duration)
        Example: [1234.5 -> 2345.6] (1111.1s)
        """
        return f"[{self.start} -> {self.end}] ({self.duration}s)"

    def __repr__(self) -> str:
        """Detailed representation of TimeRange.

        Format: TimeRange(start=value, end=value)
        Example: TimeRange(start=1234.5, end=2345.6)
        """
        return f"TimeRange(start={self.start!r}, end={self.end!r})"
