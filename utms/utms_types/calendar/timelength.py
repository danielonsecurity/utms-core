from typing import Union, Optional
from decimal import Decimal
from .protocols import TimeLength

class DecimalTimeLength:
    """Implementation of TimeLength using Decimal for precision."""
    
    def __init__(self, seconds: Union[int, float, Decimal, 'DecimalTimeLength']) -> None:
        if isinstance(seconds, DecimalTimeLength):
            self._seconds = seconds._seconds
        else:
            self._seconds = Decimal(str(seconds))
    
    def __float__(self) -> float:
        return float(self._seconds)
    
    def __int__(self) -> int:
        return int(self._seconds)
    
    # Basic arithmetic operations
    def __add__(self, other: Union['TimeLength', int, float, Decimal]) -> 'DecimalTimeLength':
        if isinstance(other, DecimalTimeLength):
            return DecimalTimeLength(self._seconds + other._seconds)
        return DecimalTimeLength(self._seconds + Decimal(str(other)))

    def __sub__(self, other: Union['TimeLength', int, float, Decimal]) -> 'DecimalTimeLength':
        if isinstance(other, DecimalTimeLength):
            return DecimalTimeLength(self._seconds - other._seconds)
        return DecimalTimeLength(self._seconds - Decimal(str(other)))

    def __mul__(self, other: Union[int, float, Decimal]) -> 'DecimalTimeLength':
        return DecimalTimeLength(self._seconds * Decimal(str(other)))

    def __truediv__(self, other: Union['TimeLength', int, float, Decimal]) -> Union['DecimalTimeLength', float]:
        if isinstance(other, DecimalTimeLength):
            return float(self._seconds / other._seconds)  # Returns ratio between lengths
        return DecimalTimeLength(self._seconds / Decimal(str(other)))

    def __floordiv__(self, other: Union['TimeLength', int, float, Decimal]) -> 'DecimalTimeLength':
        if isinstance(other, DecimalTimeLength):
            return DecimalTimeLength(self._seconds // other._seconds)
        return DecimalTimeLength(self._seconds // Decimal(str(other)))

    def __mod__(self, other: Union['TimeLength', int, float, Decimal]) -> 'DecimalTimeLength':
        if isinstance(other, DecimalTimeLength):
            return DecimalTimeLength(self._seconds % other._seconds)
        return DecimalTimeLength(self._seconds % Decimal(str(other)))

    # Right-side operations
    def __radd__(self, other: Union[int, float, Decimal]) -> 'DecimalTimeLength':
        return DecimalTimeLength(Decimal(str(other)) + self._seconds)

    def __rsub__(self, other: Union[int, float, Decimal]) -> 'DecimalTimeLength':
        return DecimalTimeLength(Decimal(str(other)) - self._seconds)

    def __rmul__(self, other: Union[int, float, Decimal]) -> 'DecimalTimeLength':
        return DecimalTimeLength(Decimal(str(other)) * self._seconds)

    def __rtruediv__(self, other: Union[int, float, Decimal]) -> 'DecimalTimeLength':
        return DecimalTimeLength(Decimal(str(other)) / self._seconds)

    def __rfloordiv__(self, other: Union[int, float, Decimal]) -> 'DecimalTimeLength':
        return DecimalTimeLength(Decimal(str(other)) // self._seconds)

    def __rmod__(self, other: Union[int, float, Decimal]) -> 'DecimalTimeLength':
        return DecimalTimeLength(Decimal(str(other)) % self._seconds)

    # In-place operations
    def __iadd__(self, other: Union['TimeLength', int, float, Decimal]) -> 'DecimalTimeLength':
        if isinstance(other, DecimalTimeLength):
            self._seconds += other._seconds
        else:
            self._seconds += Decimal(str(other))
        return self

    def __isub__(self, other: Union['TimeLength', int, float, Decimal]) -> 'DecimalTimeLength':
        if isinstance(other, DecimalTimeLength):
            self._seconds -= other._seconds
        else:
            self._seconds -= Decimal(str(other))
        return self

    def __imul__(self, other: Union[int, float, Decimal]) -> 'DecimalTimeLength':
        self._seconds *= Decimal(str(other))
        return self

    def __itruediv__(self, other: Union[int, float, Decimal]) -> 'DecimalTimeLength':
        self._seconds /= Decimal(str(other))
        return self

    def __ifloordiv__(self, other: Union[int, float, Decimal]) -> 'DecimalTimeLength':
        self._seconds //= Decimal(str(other))
        return self

    def __imod__(self, other: Union[int, float, Decimal]) -> 'DecimalTimeLength':
        self._seconds %= Decimal(str(other))
        return self

    # Unary operations
    def __neg__(self) -> 'DecimalTimeLength':
        return DecimalTimeLength(-self._seconds)

    def __pos__(self) -> 'DecimalTimeLength':
        return DecimalTimeLength(+self._seconds)

    def __abs__(self) -> 'DecimalTimeLength':
        return DecimalTimeLength(abs(self._seconds))

    def __round__(self, ndigits: Optional[int] = None) -> 'DecimalTimeLength':
        return DecimalTimeLength(round(self._seconds, ndigits) if ndigits is not None else round(self._seconds))

    # Comparison operations
    def __lt__(self, other: 'TimeLength') -> bool:
        if isinstance(other, DecimalTimeLength):
            return self._seconds < other._seconds
        return self._seconds < Decimal(str(other))

    def __le__(self, other: 'TimeLength') -> bool:
        if isinstance(other, DecimalTimeLength):
            return self._seconds <= other._seconds
        return self._seconds <= Decimal(str(other))

    def __gt__(self, other: 'TimeLength') -> bool:
        if isinstance(other, DecimalTimeLength):
            return self._seconds > other._seconds
        return self._seconds > Decimal(str(other))

    def __ge__(self, other: 'TimeLength') -> bool:
        if isinstance(other, DecimalTimeLength):
            return self._seconds >= other._seconds
        return self._seconds >= Decimal(str(other))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, DecimalTimeLength):
            return self._seconds == other._seconds
        if isinstance(other, (int, float, Decimal)):
            return self._seconds == Decimal(str(other))
        return NotImplemented


    def __str__(self) -> str:
        return f"{self._seconds}s"
    
    def __repr__(self) -> str:
        return f"DecimalTimeLength({self._seconds})"
