from utms.utms_types import (
    CalendarComponents,
    CalendarUnit,
    OptionalHyExpression,
    UnitAccessorMapping,
    UnitKey,
    UnitKeyIterator,
    UnitValue,
)


class UnitAccessor(UnitAccessorMapping):
    """Manages access to calendar units."""

    def __init__(self, units: CalendarComponents):
        self._units: CalendarComponents = units

    # Required methods for Mapping interface
    def __getitem__(self, key: UnitKey) -> UnitValue:
        return self._units[key]

    def __iter__(self) -> UnitKeyIterator:
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
    def day_of_week_fn(self) -> OptionalHyExpression:
        return self._units.get("day_of_week_fn")

    def get_all(self) -> CalendarComponents:
        """Get all units."""
        return self._units
