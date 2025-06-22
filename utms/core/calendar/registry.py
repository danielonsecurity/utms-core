from utms.core.mixins import LoggerMixin
from utms.utms_types import CalendarComponents, CalendarDefinitions, UnitDefinitions


class CalendarRegistry(LoggerMixin):
    _units: UnitDefinitions | None = None
    _calendars: CalendarDefinitions | None = None

    @classmethod
    def initialize(cls, units: UnitDefinitions, calendars: CalendarDefinitions) -> None:
        self.logger.info("Initializing calendar registry")
        self.logger.debug("Units: %s", list(units.keys()))
        self.logger.debug("Calendars: %s", list(calendars.keys()))
        cls._units = units
        cls._calendars = calendars

    @classmethod
    def get_units(cls) -> UnitDefinitions:
        if cls._units is None:
            self.logger.error("Calendar registry not initialized")
            raise RuntimeError("Calendar registry not initialized")
        return cls._units

    @classmethod
    def get_calendars(cls) -> CalendarDefinitions:
        if cls._calendars is None:
            self.logger.error("Calendar registry not initialized")
            raise RuntimeError("Calendar registry not initialized")
        return cls._calendars

    @classmethod
    def get_calendar_units(cls, name: str) -> CalendarComponents:
        """Get units for a specific calendar configuration."""
        self.logger.debug("Getting units for calendar: %s", name)

        calendars = cls.get_calendars()
        if name not in calendars:  # pylint: disable=unsupported-membership-test
            self.logger.error("Calendar %s not found", name)
            raise ValueError(f"Calendar {name} not found")

        config = calendars[name]  # pylint: disable=unsubscriptable-object
        units = cls.get_units()
        calendar_units: CalendarComponents = {}

        # Get unit mappings from the 'units' key of the config
        unit_mappings = config["units"]
        self.logger.debug("Unit mappings for %s: %s", name, unit_mappings)

        for unit_type, unit_ref in unit_mappings.items():
            unit_name = str(unit_ref)  # Convert symbol to string
            self.logger.debug("Looking up unit: %s for %s", unit_name, unit_type)

            if unit_name not in units:  # pylint: disable=unsupported-membership-test
                self.logger.error("Unit %s not found", unit_name)
                raise ValueError(f"Unit {unit_name} not found")

            calendar_units[unit_type] = units[unit_name]  # pylint: disable=unsubscriptable-object
        # Add day-of-week function if it exists
        if config.get("day_of_week"):
            self.logger.debug("Found custom day-of-week function")
            calendar_units["day_of_week_fn"] = config["day_of_week"]

        return calendar_units
