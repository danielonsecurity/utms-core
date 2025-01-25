from decimal import Decimal
from typing import Union, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .protocols import Timestamp


class DecimalTimestamp:
    """Default implementation of Timestamp using Decimal for precision."""
    
    def __init__(self, value: Union[int, float, Decimal, 'DecimalTimestamp']) -> None:
        if isinstance(value, DecimalTimestamp):
            self._value: Decimal = value._value
        else:
            self._value = Decimal(str(value))
    
    def __float__(self) -> float:
        return float(self._value)
    
    def __int__(self) -> int:
        return int(self._value)
    
    def __add__(self, other: Union['Timestamp', int, float, Decimal]) -> 'DecimalTimestamp':
        if isinstance(other, DecimalTimestamp):
            return DecimalTimestamp(self._value + other._value)
        return DecimalTimestamp(self._value + Decimal(str(other)))
    
    def __sub__(self, other: Union['Timestamp', int, float, Decimal]) -> 'DecimalTimestamp':
        if isinstance(other, DecimalTimestamp):
            return DecimalTimestamp(self._value - other._value)
        return DecimalTimestamp(self._value - Decimal(str(other)))
    
    def __truediv__(self, other: Union['Timestamp', int, float, Decimal]) -> 'DecimalTimestamp':
        if isinstance(other, DecimalTimestamp):
            return DecimalTimestamp(self._value / other._value)
        return DecimalTimestamp(self._value / Decimal(str(other)))
    
    def __floordiv__(self, other: Union['Timestamp', int, float, Decimal]) -> 'DecimalTimestamp':
        if isinstance(other, DecimalTimestamp):
            return DecimalTimestamp(self._value // other._value)
        return DecimalTimestamp(self._value // Decimal(str(other)))

    def __mul__(self, other: Union['Timestamp', int, float, Decimal]) -> 'DecimalTimestamp':
        if isinstance(other, DecimalTimestamp):
            return DecimalTimestamp(self._value * other._value)
        return DecimalTimestamp(self._value * Decimal(str(other)))

    def __mod__(self, other: Union['Timestamp', int, float, Decimal]) -> 'DecimalTimestamp':
        if isinstance(other, DecimalTimestamp):
            return DecimalTimestamp(self._value % other._value)
        return DecimalTimestamp(self._value % Decimal(str(other)))
    

    def __lt__(self, other: Union['Timestamp', int, float, Decimal]) -> bool:
        if isinstance(other, DecimalTimestamp):
            return self._value < other._value
        return self._value < Decimal(str(other))
    
    def __le__(self, other: Union['Timestamp', int, float, Decimal]) -> bool:
        if isinstance(other, DecimalTimestamp):
            return self._value <= other._value
        return self._value <= Decimal(str(other))
    
    def __gt__(self, other: Union['Timestamp', int, float, Decimal]) -> bool:
        if isinstance(other, DecimalTimestamp):
            return self._value > other._value
        return self._value > Decimal(str(other))
    
    def __ge__(self, other: Union['Timestamp', int, float, Decimal]) -> bool:
        if isinstance(other, DecimalTimestamp):
            return self._value >= other._value
        return self._value >= Decimal(str(other))
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, DecimalTimestamp):
            return self._value == other._value
        if isinstance(other, (int, float, Decimal)):
            return self._value == Decimal(str(other))
        return NotImplemented
    
    def __radd__(self, other: Union[int, float, Decimal]) -> 'DecimalTimestamp':
        return DecimalTimestamp(Decimal(str(other)) + self._value)

    def __rsub__(self, other: Union[int, float, Decimal]) -> 'DecimalTimestamp':
        return DecimalTimestamp(Decimal(str(other)) - self._value)

    def __rmul__(self, other: Union[int, float, Decimal]) -> 'DecimalTimestamp':
        return DecimalTimestamp(Decimal(str(other)) * self._value)

    def __rtruediv__(self, other: Union[int, float, Decimal]) -> 'DecimalTimestamp':
        return DecimalTimestamp(Decimal(str(other)) / self._value)

    def __rfloordiv__(self, other: Union[int, float, Decimal]) -> 'DecimalTimestamp':
        return DecimalTimestamp(Decimal(str(other)) // self._value)

    def __rmod__(self, other: Union[int, float, Decimal]) -> 'DecimalTimestamp':
        return DecimalTimestamp(Decimal(str(other)) % self._value)

    def __neg__(self) -> 'DecimalTimestamp':
        return DecimalTimestamp(-self._value)

    def __pos__(self) -> 'DecimalTimestamp':
        return DecimalTimestamp(+self._value)

    def __abs__(self) -> 'DecimalTimestamp':
        return DecimalTimestamp(abs(self._value))

    def __round__(self, ndigits: Optional[int] = None) -> 'DecimalTimestamp':
        return DecimalTimestamp(round(self._value, ndigits) if ndigits is not None else round(self._value))

    def __iadd__(self, other: Union['Timestamp', int, float, Decimal]) -> 'DecimalTimestamp':
        if isinstance(other, DecimalTimestamp):
            self._value += other._value
        else:
            self._value += Decimal(str(other))
        return self

    def __isub__(self, other: Union['Timestamp', int, float, Decimal]) -> 'DecimalTimestamp':
        if isinstance(other, DecimalTimestamp):
            self._value -= other._value
        else:
            self._value -= Decimal(str(other))
        return self

    def __imul__(self, other: Union['Timestamp', int, float, Decimal]) -> 'DecimalTimestamp':
        if isinstance(other, DecimalTimestamp):
            self._value *= other._value
        else:
            self._value *= Decimal(str(other))
        return self

    def __itruediv__(self, other: Union['Timestamp', int, float, Decimal]) -> 'DecimalTimestamp':
        if isinstance(other, DecimalTimestamp):
            self._value /= other._value
        else:
            self._value /= Decimal(str(other))
        return self

    def __ifloordiv__(self, other: Union['Timestamp', int, float, Decimal]) -> 'DecimalTimestamp':
        if isinstance(other, DecimalTimestamp):
            self._value //= other._value
        else:
            self._value //= Decimal(str(other))
        return self

    def __imod__(self, other: Union['Timestamp', int, float, Decimal]) -> 'DecimalTimestamp':
        if isinstance(other, DecimalTimestamp):
            self._value %= other._value
        else:
            self._value %= Decimal(str(other))
        return self



    def __str__(self) -> str:
        return str(self._value)
    
    def __repr__(self) -> str:
        return f"DecimalTimestamp({self._value})"
