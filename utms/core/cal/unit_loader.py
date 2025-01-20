from hy.models import Expression, List, Symbol

from utms.resolvers import CalendarResolver

from .cal_unit import CalendarUnit

_resolver = CalendarResolver()


def parse_unit_definitions(units_data):
    """Parse Hy unit definitions into a dictionary of unit specifications."""
    units = {}
    for unit_def_expr in units_data:
        if not isinstance(unit_def_expr, Expression) or unit_def_expr[0] != Symbol("defunit"):
            raise ValueError("Invalid unit definition format.")

        _, unit_name_sym, *unit_properties = unit_def_expr
        unit_name = str(unit_name_sym)
        unit_kwargs = {}

        for prop_expr in unit_properties:
            if isinstance(prop_expr, Expression):
                prop_name = str(prop_expr[0])
                prop_value = prop_expr[1]
                unit_kwargs[prop_name] = prop_value
            else:
                raise ValueError(f"Unexpected item type in unit properties: {type(prop_expr)}")

        units[unit_name] = {"name": unit_name, "kwargs": unit_kwargs}

    return units


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
    parsed_units = parse_unit_definitions(units_data)
    units = initialize_units(parsed_units)
    resolve_unit_properties(units, timestamp)

    # Calculate indexes after all properties are resolved
    for unit in units.values():
        unit.calculate_index(timestamp)

    return units
