from collections.abc import Mapping
from typing import Dict, Optional
from utms.utms_types import CalendarUnit, HyExpression

class UnitAccessor(Mapping):
    """Manages access to calendar units."""
    
    def __init__(self, units: Dict[str, CalendarUnit]):
        self._units = units

    # Required methods for Mapping interface
    def __getitem__(self, key: str) -> CalendarUnit:
        return self._units[key]

    def __iter__(self):
        return iter(self._units)

    def __len__(self) -> int:
        return len(self._units)

    @property
    def year(self) -> CalendarUnit:
        return self._units["year"]

    @property
    def month(self) -> CalendarUnit:
        return self._units["month"]

    @property
    def week(self) -> CalendarUnit:
        return self._units["week"]

    @property
    def day(self) -> CalendarUnit:
        return self._units["day"]

    @property
    def day_of_week_fn(self) -> Optional[HyExpression]:
        return self._units.get("day_of_week_fn")

    def get_all(self) -> Dict[str, CalendarUnit]:
        """Get all units."""
        return self._units
