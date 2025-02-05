"""This module defines the `Config` class, which manages the configuration of
time units and datetime anchors.

The `Config` class is responsible for populating predefined time units and datetime anchors.  It
uses the `UnitManager` class to manage time units such as Planck Time, Picoseconds, and
Milliseconds, and the `AnchorManager` class to manage datetime anchors like Unix Time, CE Time, and
Big Bang Time.

Constants from the `constants` module are used to define the values for the time units and anchors.

Modules:
- `utms.constants`: Contains predefined constants for time and datetime values.
- `utms.anchors`: Contains the `AnchorManager` class for managing datetime anchors.
- `utms.units`: Contains the `UnitManager` class for managing time units.

Usage:
- Instantiate the `Config` class to initialize the units and anchors with predefined values.
"""

import importlib.resources
import json
import os
import re
import shutil
import socket
import sys
from datetime import datetime, timezone
from decimal import Decimal
from time import time
from typing import Any, List, Optional, Tuple, Union

import appdirs
import ntplib

from ..utms_types import (
    AnchorManagerProtocol,
    ConfigData,
    ConfigPath,
    ConfigProtocol,
    ConfigValue,
    NestedConfig,
    OptionalString,
    FixedUnitManagerProtocol,
    is_expression,
)

from . import constants
from .anchors import AnchorConfig, AnchorManager
from .units import FixedUnitManager
from ..resolvers import ConfigResolver, VariableResolver, evaluate_hy_file, FixedUnitResolver, AnchorResolver

from ..utils import get_logger, hy_to_python, format_hy_value, get_ntp_date, set_log_level

from ..loaders.unit_loader import parse_calendar_definitions, parse_unit_definitions, initialize_units, resolve_unit_properties
from ..loaders.anchor_loader import parse_anchor_definitions, initialize_anchors
from ..loaders.variable_loader import process_variables

logger = get_logger("core.config")



 
class Config(ConfigProtocol):
    """Configuration class that manages units and anchors for time and datetime
    references.

    This class is responsible for populating time units and datetime anchors based on predefined
    constants.  It uses the `AnchorManager` and `UnitManager` classes to add relevant time units and
    datetime anchors.
    """

    def __init__(self) -> None:
        """Initializes the configuration by creating instances of
        `AnchorManager` and `UnitManager`, then populating them with units and
        anchors.

        This method calls `populate_units()` to add time units and
        `populate_anchors()` to add datetime anchors.
        """
        self._utms_dir = appdirs.user_config_dir(constants.APP_NAME, constants.COMPANY_NAME)
        # Ensure the config directory exists
        os.makedirs(self.utms_dir, exist_ok=True)
        self.init_resources()
        self._data: NestedConfig = {}  # = self.load()

        self.resolver = ConfigResolver()
        self._variable_resolver = VariableResolver
        self._variables = {}
        self._load_variables()
        self._load_hy_config()
        set_log_level(self.loglevel)
        self._fixed_units: FixedUnitManagerProtocol = FixedUnitManager()
        self._calendar_units = {}
        self._calendars = {}
        self._anchors: AnchorManagerProtocol = AnchorManager(self.units)
        self._load_fixed_units()
        self._load_calendar_units()
        self.populate_dynamic_anchors()
        self._load_anchors()


    def _load_hy_config(self) -> None:
        config_hy = os.path.join(self.utms_dir, "config.hy")
        if os.path.exists(config_hy):
            try:
                expressions = evaluate_hy_file(config_hy)
                if expressions:
                    config = self.resolver.resolve_config_property(expressions[0])
                    self._data = config
            except Exception as e:
                logger.error("Error loading Hy config: %s", e)

    def _save_hy_config(self) -> None:
        """Save current configuration to config.hy."""
        config_hy = os.path.join(self.utms_dir, "config.hy")

        settings = []
        for key, value in self._data.items():
            formatted_value = format_hy_value(value)
            settings.append(f"  '({key} {formatted_value})")

        content = [
            ";; This file is managed by UTMS - do not edit manually",
            "(custom-set-config",
            *sorted(settings),
            ")",
        ]

        with open(config_hy, "w") as f:
            f.write("\n".join(content))

    def get_value(self, key: ConfigPath, pretty: bool = False) -> ConfigValue:
        """Get value from configuration."""
        value = self._data.get(key)

        if value is not None:
            value = hy_to_python(value)

        if pretty and value is not None:
            return json.dumps(value, indent=4, sort_keys=True)

        return value

    def has_value(self, key: ConfigPath) -> bool:
        return key in self._data

    def set_value(self, key: ConfigPath, value: ConfigValue) -> None:
        self._data[key] = value
        self._save_hy_config()

    def print(self, filter_key: OptionalString = None) -> None:
        if filter_key:
            try:
                pretty_result = self.get_value(filter_key, pretty=True)
                print(pretty_result)
            except KeyError as e:
                print(f"Error: {e}")
        else:
            print(json.dumps(self.data, indent=4, sort_keys=True))

    def _load_variables(self) -> None:
        variables_hy = os.path.join(self.utms_dir, "variables.hy")
        if os.path.exists(variables_hy):
            expressions = evaluate_hy_file(variables_hy)
            if expressions:
                self._variables = process_variables(expressions)

    def init_resources(self) -> None:
        """Copy resources to the user config directory if they do not already
        exist."""
        resources = [
            "system_prompt.txt",
            "config.json",
            "anchors.json",
            "units.json",
            "calendar_units.hy",
            "fixed_units.hy",
        ]
        for item in resources:
            source_file = importlib.resources.files("utms.resources") / item
            destination_file = os.path.join(self.utms_dir, item)

            # Copy only if the destination file does not exist
            if not os.path.exists(destination_file):
                shutil.copy(str(source_file), destination_file)

    def _load_anchors(self) -> None:
        anchors_file = os.path.join(self.utms_dir, "anchors.hy")
        if os.path.exists(anchors_file):
            anchor_expressions = evaluate_hy_file(anchors_file)
            if anchor_expressions:
                parsed_anchor_defs = parse_anchor_definitions(anchor_expressions)
                anchor_instances = initialize_anchors(parsed_anchor_defs, self._variables)
                for anchor in anchor_instances.values():
                    self._anchors.add_anchor(anchor)

    def load_anchors(self) -> None:
        """Loads anchors from the 'anchors.json' file and populates the anchors
        dynamically.

        This method reads the `anchors.json` file, parses its content, and uses the `AnchorManager`
        to add each anchor to the configuration.
        """
        anchors_file = os.path.join(self.utms_dir, "anchors.json")

        if os.path.exists(anchors_file):
            with open(anchors_file, "r", encoding="utf-8") as f:
                anchors_data = json.load(f)

            # Iterate through the anchors data and add each anchor
            for key, anchor in anchors_data.items():
                name = anchor.get("name")
                timestamp = anchor.get("timestamp")
                groups = anchor.get("groups")
                precision = anchor.get("precision")
                formats = anchor.get("formats")
                # Add anchor using the details loaded from the JSON
                anchor_config = AnchorConfig(
                    label=key,
                    name=name,
                    value=Decimal(timestamp),
                    groups=groups,
                    precision=Decimal(precision) if precision else None,
                    # breakdowns=breakdowns,
                    formats=formats if formats else ["CALENDAR"],
                )
                self.anchors.add_anchor(anchor_config)

        else:
            print(f"Error: '{anchors_file}' not found.")

    def save_anchors(self) -> None:
        """Saves the current anchors to the 'anchors.json' file.

        This method serializes the anchors stored in the `self.anchors` set
        and writes them to the `anchors.json` file.
        """
        anchors_file = os.path.join(self.utms_dir, "anchors.json")
        anchors_data = {}

        # Iterate through each anchor and prepare data for saving
        for anchor in self.anchors:
            anchor_info = {
                "name": anchor.name,
                "timestamp": float(anchor.value),
                "groups": anchor.groups,
                "precision": float(anchor.precision) if anchor.precision else None,
                "breakdowns": anchor.breakdowns,
            }
            anchors_data[anchor.label] = anchor_info

        # Write the serialized anchors data to the file
        try:
            with open(anchors_file, "w", encoding="utf-8") as f:
                json.dump(anchors_data, f, ensure_ascii=False, indent=4)
            print(f"Anchors successfully saved to '{anchors_file}'")
        except (FileNotFoundError, PermissionError, OSError) as e:
            print(f"Error saving anchors: {e}")
        except json.JSONDecodeError as e:
            print(f"Error serializing data to JSON: {e}")

    def _load_fixed_units(self) -> None:
        units_hy = os.path.join(self.utms_dir, "fixed_units.hy")
        
        if os.path.exists(units_hy):
            try:

                resolver = FixedUnitResolver()
                expressions = evaluate_hy_file(units_hy)
                
                # Process each unit definition
                for expr in expressions:
                    if expr:  # Skip empty lines
                        unit_data = resolver.resolve(expr)

                        if unit_data:
                            for label, unit in unit_data.items():
                                self.units.add_unit(
                                    unit['name'],
                                    label,
                                    Decimal(unit['value']),
                                    unit.get('groups', [])
                                )
                
                logger.info("Loaded fixed units from Hy file")
            except Exception as e:
                logger.error("Error loading fixed units: %s", e)

    def _load_calendar_units(self) -> None:
        units_hy = os.path.join(self.utms_dir, "calendar_units.hy")
        
        if os.path.exists(units_hy):
            try:
                expressions = evaluate_hy_file(units_hy)
                parsed_calendar_units = parse_unit_definitions(expressions)
                calendar_units = initialize_units(parsed_calendar_units)
                calendars = parse_calendar_definitions(expressions)
                resolve_unit_properties(calendar_units)
                self._calendar_units = calendar_units
                self._calendars = calendars
                logger.info("Loaded calendar units from Hy file")
            except Exception as e:
                logger.error("Error loading calendar units: %s", e)


    def save_units(self) -> None:
        """Saves the current time units to fixed_units.hy."""
        units_hy = os.path.join(self.utms_dir, "fixed_units.hy")

        content = [
            ";; Fixed Time Units",
            ";; This file is managed by UTMS - do not edit manually",
            ""
        ]

        # Iterate through each unit and format for Hy
        for unit_abbreviation in self.units:
            unit = self.units[unit_abbreviation]
            content.append(f"""(def-fixed-unit {unit_abbreviation}
      :name "{unit.name}"
      :value "{unit.value}")""")
            content.append("")  # Empty line between units

        try:
            with open(units_hy, 'w', encoding='utf-8') as f:
                f.write("\n".join(content))
            logger.info("Units successfully saved to '%s'", units_hy)
        except (FileNotFoundError, PermissionError, OSError) as e:
            logger.error("Error saving units: %s", e)


    # def populate_dynamic_anchors(self) -> None:
    #     """Populates the `AnchorManager` instance with predefined datetime
    #     anchors.

    #     This method adds various datetime anchors such as Unix Time, CE Time, and Big Bang Time,
    #     using the `add_datetime_anchor` and `add_decimal_anchor` methods of the `AnchorManager`
    #     instance.  Each anchor is added with its name, symbol, and corresponding datetime value.
    #     """

    #     self.anchors.add_anchor(
    #         AnchorConfig(
    #             label="NT",
    #             name=f"Now Time ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})",
    #             value=get_ntp_date(),
    #             groups=["default", "dynamic", "modern"],
    #         )
    #     )
    #     self.anchors.add_anchor(
    #         AnchorConfig(
    #             label="DT",
    #             name=f"Day Time ({datetime.now().strftime('%Y-%m-%d 00:00:00')})",
    #             value=datetime(
    #                 datetime.now().year,
    #                 datetime.now().month,
    #                 datetime.now().day,
    #                 tzinfo=datetime.now().astimezone().tzinfo,
    #             ),
    #             breakdowns=[["dd", "cd", "s", "ms"], ["h", "m", "s", "ms"], ["KS", "s", "ms"]],
    #             groups=["dynamic", "modern"],
    #         )
    #     )
    #     self.anchors.add_anchor(
    #         AnchorConfig(
    #             label="MT",
    #             name=f"Month Time ({datetime.now().strftime('%Y-%m-01 00:00:00')})",
    #             value=datetime(
    #                 datetime.now().year,
    #                 datetime.now().month,
    #                 1,
    #                 tzinfo=datetime.now().astimezone().tzinfo,
    #             ),
    #             breakdowns=[
    #                 ["d", "dd", "cd", "s", "ms"],
    #                 ["w", "d", "dd", "cd", "s", "ms"],
    #                 ["MS", "KS", "s", "ms"],
    #             ],
    #             groups=["dynamic", "modern"],
    #         )
    #     )

    #     self.anchors.add_anchor(
    #         AnchorConfig(
    #             label="YT",
    #             name=f"Year Time ({datetime.now().strftime('%Y-01-01 00:00:00')})",
    #             value=datetime(
    #                 datetime.now().year, 1, 1, tzinfo=datetime.now().astimezone().tzinfo
    #             ),
    #             breakdowns=[
    #                 ["d", "dd", "cd", "s", "ms"],
    #                 ["w", "d", "dd", "cd", "s", "ms"],
    #                 ["M", "d", "dd", "cd", "s", "ms"],
    #                 ["MS", "KS", "s", "ms"],
    #             ],
    #             groups=["dynamic", "modern"],
    #         )
    #     )

    @property
    def utms_dir(self) -> str:
        return str(self._utms_dir)

    @property
    def data(self) -> ConfigData:
        return self._data

    @property
    def units(self) -> FixedUnitManagerProtocol:
        return self._fixed_units

    @property
    def anchors(self) -> AnchorManagerProtocol:
        return self._anchors

    @property
    def loglevel(self):
        return self.get_value("loglevel")
