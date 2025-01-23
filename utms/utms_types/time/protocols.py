from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, Union, List, Dict, Any, Protocol


from typing import Protocol, Optional, Union, Tuple
from decimal import Decimal

class TimeCalculator(Protocol):
    """Protocol for time-based calculations."""

    def add_time(
        self,
        timestamp: float,
        amount: Union[int, float, Decimal],
        unit: str,
        timezone: Optional[float] = None
    ) -> float:
        """Add time to timestamp.
        
        Args:
            timestamp: Base timestamp
            amount: Amount to add
            unit: Unit of time ('seconds', 'minutes', 'hours', 'days', etc.)
            timezone: Optional timezone offset
            
        Returns:
            New timestamp after addition
        """
        ...

    def subtract_time(
        self,
        timestamp: float,
        amount: Union[int, float, Decimal],
        unit: str,
        timezone: Optional[float] = None
    ) -> float:
        """Subtract time from timestamp.
        
        Args:
            timestamp: Base timestamp
            amount: Amount to subtract
            unit: Unit of time ('seconds', 'minutes', 'hours', 'days', etc.)
            timezone: Optional timezone offset
            
        Returns:
            New timestamp after subtraction
        """
        ...

    def diff_time(
        self,
        timestamp1: float,
        timestamp2: float,
        unit: str,
        timezone: Optional[float] = None
    ) -> Union[int, float, Decimal]:
        """Calculate time difference between timestamps.
        
        Args:
            timestamp1: First timestamp
            timestamp2: Second timestamp
            unit: Unit for result ('seconds', 'minutes', 'hours', 'days', etc.)
            timezone: Optional timezone offset
            
        Returns:
            Time difference in specified unit
        """
        ...

    def normalize_time(
        self,
        timestamp: float,
        unit: str,
        timezone: Optional[float] = None
    ) -> float:
        """Normalize timestamp to unit boundaries.
        
        Args:
            timestamp: Timestamp to normalize
            unit: Unit to normalize to ('day', 'hour', etc.)
            timezone: Optional timezone offset
            
        Returns:
            Normalized timestamp
        """
        ...

    def split_time(
        self,
        timestamp: float,
        timezone: Optional[float] = None
    ) -> Tuple[int, int, int, int, int, int]:
        """Split timestamp into components.
        
        Args:
            timestamp: Timestamp to split
            timezone: Optional timezone offset
            
        Returns:
            Tuple of (year, month, day, hour, minute, second)
        """
        ...

    def combine_time(
        self,
        year: int,
        month: int,
        day: int,
        hour: int = 0,
        minute: int = 0,
        second: int = 0,
        timezone: Optional[float] = None
    ) -> float:
        """Combine time components into timestamp.
        
        Args:
            year: Year component
            month: Month component
            day: Day component
            hour: Hour component
            minute: Minute component
            second: Second component
            timezone: Optional timezone offset
            
        Returns:
            Combined timestamp
        """
        ...
