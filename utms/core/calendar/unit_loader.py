from hy.models import Expression, List, Symbol

from utms.resolvers import CalendarResolver
from utms.utils import get_logger
from .calendar_unit import CalendarUnit

logger = get_logger('core.calendar.unit_loader')

_resolver = CalendarResolver()



def parse_unit_definitions(units_data):
    """Parse Hy unit definitions into a dictionary of unit specifications."""
    units = {}
    logger.debug("Starting to parse unit definitions")
    
    for unit_def_expr in units_data:
        if not isinstance(unit_def_expr, Expression):
            logger.debug(f"Skipping non-Expression: {unit_def_expr}")
            continue
            
        if str(unit_def_expr[0]) != "defunit":
            logger.debug(f"Skipping non-defunit expression: {unit_def_expr[0]}")
            continue

        _, unit_name_sym, *unit_properties = unit_def_expr
        unit_name = str(unit_name_sym)
        logger.debug(f"Processing unit: {unit_name} (type: {type(unit_name_sym)})")
        
        unit_kwargs = {}
        for prop_expr in unit_properties:
            if isinstance(prop_expr, Expression):
                prop_name = str(prop_expr[0])
                prop_value = prop_expr[1]
                unit_kwargs[prop_name] = prop_value
            else:
                logger.error(f"Unexpected item type in unit properties: {type(prop_expr)}")
                raise ValueError(f"Unexpected item type in unit properties: {type(prop_expr)}")

        units[unit_name] = {"name": unit_name, "kwargs": unit_kwargs}
        logger.info(f"Added unit: {unit_name}")

    logger.debug(f"Finished parsing units. Total: {len(units)}")
    return units


def parse_calendar_definitions(units_data):
    """Parse Hy calendar definitions into a dictionary of calendar configurations."""
    calendars = {}
    logger.debug("Starting to parse calendar definitions")
    
    for expr in units_data:
        if not isinstance(expr, Expression):
            continue
            
        if str(expr[0]) != "defcalendar":
            continue
            
        _, cal_name_sym, *properties = expr
        calendar_name = str(cal_name_sym)
        logger.debug(f"Found calendar definition: {calendar_name}")
        
        unit_config = {}
        day_of_week = None
        for prop in properties:
            if str(prop[0]) == "day-of-week":
                logger.debug(f"Found day-of-week function for {calendar_name}")
                day_of_week = prop[1]
            else:
                unit_type = str(prop[0])
                unit_ref = prop[1]
                logger.debug(f"  Unit mapping: {unit_type} -> {unit_ref}")
                unit_config[unit_type] = unit_ref
            
            
        calendars[calendar_name] = {
            'units': unit_config,
            'day_of_week': day_of_week
        }
        logger.info(f"Added calendar configuration: {calendar_name}")
        
    logger.debug(f"Finished parsing calendars. Total: {len(calendars)}")
    return calendars

def get_calendar_units(name, units, calendars):
    """Get the units for a specific calendar configuration."""
    logger.debug(f"Getting units for calendar: {name}")
    
    if name not in calendars:
        logger.error(f"Calendar '{name}' not found")
        raise ValueError(f"Calendar '{name}' not found")
        
    config = calendars[name]
    calendar_units = {}
    
    for unit_type, unit_ref in config.items():
        unit_name = str(unit_ref)  # Convert symbol to string
        logger.debug(f"Looking up unit: {unit_name} for {unit_type}")
        
        if unit_name not in units:
            logger.error(f"Unit '{unit_name}' not found")
            raise ValueError(f"Unit '{unit_name}' not found")
            
        calendar_units[unit_type] = units[unit_name]
        
    return calendar_units


def initialize_units(parsed_units):
    """Create CalendarUnit instances from parsed definitions."""
    units = {}
    for unit_name, unit_info in parsed_units.items():
        unit_kwargs = unit_info["kwargs"]
        units[unit_name] = CalendarUnit(name=unit_name, units=units, **unit_kwargs)
    return units


def resolve_unit_properties(units, timestamp):
    """Resolve all Hy expressions in unit properties."""
    for unit in list(units.values()):
        for prop_name, prop_value in unit.__dict__.items():
            if prop_name != "name" and isinstance(prop_value, (Expression, Symbol, List)):
                resolved_value = _resolver.resolve_unit_property(prop_value, units, unit, timestamp)
                setattr(unit, prop_name, resolved_value)



def process_units(units_data, timestamp):
    """Process Hy unit definitions into fully initialized calendar units."""
    logger.debug("Starting process_units")
    parsed_units = parse_unit_definitions(units_data)
    logger.debug(f"Parsed units: {list(parsed_units.keys())}")
    units = initialize_units(parsed_units)
    logger.debug(f"Initialized units: {list(units.keys())}")
    resolve_unit_properties(units, timestamp)
    logger.debug("Resolved unit properties")

    # Calculate indexes after all properties are resolved
    for unit in units.values():
        unit.calculate_index(timestamp)

    return units
