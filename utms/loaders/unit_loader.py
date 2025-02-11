from ..core.calendar.calendar_unit import CalendarUnit
from ..resolvers import CalendarResolver
from ..utils import get_logger
from ..utms_types import (
    CalendarDefinitions,
    ExpressionList,
    OptionalHyExpression,
    PropertyDict,
    TimeStamp,
    UnitDefinitions,
    UnitKwargs,
    UnitMappings,
    UnitsDict,
    is_expression,
    is_hy_compound,
    to_unit_type,
)

logger = get_logger("core.calendar.unit_loader")

_resolver = CalendarResolver()


def parse_unit_definitions(units_data: ExpressionList) -> UnitDefinitions:
    """Parse Hy unit definitions into a dictionary of unit specifications."""
    units: UnitDefinitions = {}
    logger.debug("Starting to parse unit definitions")

    for unit_def_expr in units_data:
        if not is_expression(unit_def_expr):
            logger.debug("Skipping non-Expression: %s", unit_def_expr)
            continue

        if str(unit_def_expr[0]) != "def-calendar-unit":
            logger.debug("Skipping non-defunit expression: %s", unit_def_expr[0])
            continue

        _, unit_name_sym, *unit_properties = unit_def_expr
        unit_name = str(unit_name_sym)
        logger.debug("Processing unit: %s (type: %s)", unit_name, type(unit_name_sym))

        unit_kwargs_dict: PropertyDict = {}
        for prop_expr in unit_properties:
            if is_expression(prop_expr):
                prop_name = str(prop_expr[0])
                prop_value = prop_expr[1]
                unit_kwargs_dict[prop_name] = prop_value
            else:
                logger.error("Unexpected item type in unit properties: %s", type(prop_expr))
                raise ValueError(f"Unexpected item type in unit properties: {type(prop_expr)}")
        unit_kwargs = UnitKwargs(
            length=unit_kwargs_dict.get("length"),
            timezone=unit_kwargs_dict.get("timezone"),
            start=unit_kwargs_dict.get("start"),
            names=unit_kwargs_dict.get("names"),
            offset=unit_kwargs_dict.get("offset"),
            index=unit_kwargs_dict.get("index"),
        )

        units[unit_name] = {"name": unit_name, "kwargs": unit_kwargs}
        logger.info("Added unit: %s", unit_name)

    logger.debug("Finished parsing units. Total: %s", len(units))
    return units


def parse_calendar_definitions(units_data: ExpressionList) -> CalendarDefinitions:
    """Parse Hy calendar definitions into a dictionary of calendar configurations."""
    calendars: CalendarDefinitions = {}
    logger.debug("Starting to parse calendar definitions")

    for expr in units_data:
        if not is_expression(expr):
            continue

        if str(expr[0]) != "def-calendar":
            continue

        _, cal_name_sym, *properties = expr
        calendar_name = str(cal_name_sym)
        logger.debug("Found calendar definition: {calendar_name}")

        unit_config: UnitMappings = {}
        day_of_week: OptionalHyExpression = None
        for prop in properties:
            if str(prop[0]) == "day-of-week":
                logger.debug("Found day-of-week function for %s", calendar_name)
                day_of_week = prop[1]
            else:
                try:
                    unit_type = to_unit_type(str(prop[0]))
                    unit_ref = prop[1]
                    logger.debug("  Unit mapping: %s -> %s", unit_type, unit_ref)
                    unit_config[unit_type] = unit_ref
                except ValueError:
                    logger.error("Invalid unit type %s:", str(prop[0]))
                    raise

        calendars[calendar_name] = {"units": unit_config, "day_of_week": day_of_week}
        logger.info("Added calendar configuration: %s", calendar_name)

    logger.debug("Finished parsing calendars. Total: %s", len(calendars))
    return calendars


def initialize_units(parsed_units: UnitDefinitions) -> UnitsDict:
    """Create CalendarUnit instances from parsed definitions."""
    units: UnitsDict = {}
    for unit_name, unit_info in parsed_units.items():
        unit_kwargs = unit_info["kwargs"]
        units[unit_name] = CalendarUnit(unit_name, units, unit_kwargs)
    return units


def resolve_unit_properties(units: UnitsDict) -> None:
    """Resolve all Hy expressions in unit properties."""
    for unit in units.values():
        for prop_name, prop_value in unit.get_all_properties().items():
            if prop_name != "name" and is_hy_compound(prop_value):
                resolved_value = _resolver.resolve_unit_property(prop_value, unit)
                unit.set_property(prop_name, resolved_value)


def process_units(units_data: ExpressionList, timestamp: TimeStamp) -> UnitsDict:
    """Process Hy unit definitions into fully initialized calendar units."""
    logger.debug("Starting process_units")
    parsed_units = parse_unit_definitions(units_data)
    logger.debug("Parsed units: %s", list(parsed_units.keys()))
    units = initialize_units(parsed_units)
    logger.debug("Initialized units: %s", list(units.keys()))
    resolve_unit_properties(units)
    logger.debug("Resolved unit properties")

    # Calculate indexes after all properties are resolved
    for unit in units.values():
        unit.calculate_index(timestamp)

    return units
