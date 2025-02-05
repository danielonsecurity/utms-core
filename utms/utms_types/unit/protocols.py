import argparse
from decimal import Decimal
from typing import Dict, Iterator, Optional, Protocol, Union


class UnitProtocol(Protocol):
    """Protocol defining the interface for Unit class."""

    @property
    def name(self) -> str: ...

    @property
    def abbreviation(self) -> str: ...

    @property
    def value(self) -> Decimal: ...

    def convert_to(self, other: "UnitProtocol", value: Decimal) -> Decimal:
        """Convert value from this unit to another unit."""
        ...

    def __eq__(self, other: object) -> bool: ...

    def __lt__(self, other: object) -> bool: ...

    def __str__(self) -> str: ...

    def __repr__(self) -> str: ...


class FixedUnitManagerProtocol(Protocol):
    """Protocol defining the interface for UnitManager class."""

    def add_unit(self, name: str, abbreviation: str, value: Decimal, groups) -> None:
        """Add a new time unit."""
        ...

    def get_value(self, abbreviation: str) -> Decimal:
        """Get unit value by abbreviation."""
        ...

    def get_unit(self, abbreviation: str) -> Optional[UnitProtocol]:
        """Get unit by abbreviation."""
        ...

    def get_all_units(self) -> Dict[str, UnitProtocol]:
        """Get all units."""
        ...

    def print(self, args: argparse.Namespace) -> None:
        """Print all units."""
        ...

    def print_conversion_table(
        self, center_unit: str, num_columns: int = 5, num_rows: int = 100
    ) -> None:
        """Print conversion table."""
        ...

    def convert_units(self, args: argparse.Namespace) -> None:
        """Convert units based on arguments."""
        ...

    def __iter__(self) -> Iterator[str]: ...

    def __getitem__(self, index: Union[int, str]) -> UnitProtocol: ...

    def __len__(self) -> int: ...
