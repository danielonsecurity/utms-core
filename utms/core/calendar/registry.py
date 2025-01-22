from utms.utils import get_logger

logger = get_logger('core.calendar.calendar_registry')

class CalendarRegistry:
    _units = None
    _calendars = None
    
    @classmethod
    def initialize(cls, units, calendars):
        logger.info("Initializing calendar registry")
        logger.debug(f"Units: {list(units.keys())}")
        logger.debug(f"Calendars: {list(calendars.keys())}")
        cls._units = units
        cls._calendars = calendars
    
    @classmethod
    def get_units(cls):
        if cls._units is None:
            logger.error("Calendar registry not initialized")
            raise RuntimeError("Calendar registry not initialized")
        return cls._units
    
    @classmethod
    def get_calendars(cls):
        if cls._calendars is None:
            logger.error("Calendar registry not initialized")
            raise RuntimeError("Calendar registry not initialized")
        return cls._calendars
    
    @classmethod
    def get_calendar_units(cls, name):
        """Get units for a specific calendar configuration."""
        logger.debug(f"Getting units for calendar: {name}")
        
        calendars = cls.get_calendars()
        if name not in calendars:
            logger.error(f"Calendar '{name}' not found")
            raise ValueError(f"Calendar '{name}' not found")
            
        config = calendars[name]
        units = cls.get_units()
        calendar_units = {}

        # Get unit mappings from the 'units' key of the config
        unit_mappings = config['units']
        logger.debug(f"Unit mappings for {name}: {unit_mappings}")
    
        for unit_type, unit_ref in unit_mappings.items():
            unit_name = str(unit_ref)  # Convert symbol to string
            logger.debug(f"Looking up unit: {unit_name} for {unit_type}")

            if unit_name not in units:
                logger.error(f"Unit '{unit_name}' not found")
                raise ValueError(f"Unit '{unit_name}' not found")

            calendar_units[unit_type] = units[unit_name]
        # Add day-of-week function if it exists
        if config.get('day_of_week'):
            logger.debug("Found custom day-of-week function")
            calendar_units['day_of_week_fn'] = config['day_of_week']

        return calendar_units

    @classmethod
    def get_day_of_week_fn(cls, name):
        """Get the custom day-of-week function for a calendar if it exists."""
        logger.debug(f"Getting day-of-week function for calendar: {name}")

        calendars = cls.get_calendars()
        if name not in calendars:
            logger.error(f"Calendar '{name}' not found")
            raise ValueError(f"Calendar '{name}' not found")

        config = calendars[name]
        return config.get('day_of_week')
