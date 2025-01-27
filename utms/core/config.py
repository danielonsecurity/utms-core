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

from utms.utms_types import (
    AnchorManagerProtocol,
    ConfigData,
    ConfigPath,
    ConfigProtocol,
    ConfigValue,
    NestedConfig,
    OptionalString,
    UnitManagerProtocol,
)
from utms.utils import hy_to_python, format_hy_value

from . import constants
from .anchors import AnchorConfig, AnchorManager
from .units import UnitManager
from ..resolvers import ConfigResolver, evaluate_hy_file

from .config_loader import get_logger, is_hy_compound, parse_config_definitions, resolve_config_values

logger = get_logger("core.config")

def get_ntp_date() -> datetime:
    """Retrieves the current date in datetime format using an NTP (Network Time
    Protocol) server.

    This function queries an NTP server (default is "pool.ntp.org") to
    get the accurate current time. The NTP timestamp is converted to a
    UTC `datetime` object and formatted as a date string. If the NTP
    request fails (due to network issues or other errors), the function
    falls back to the system time.

    Returns:
        str: The current date in 'YYYY-MM-DD' format, either from the
        NTP server or the system clock as a fallback.

    Exceptions:
        - If the NTP request fails, the system time is used instead.
    """
    client = ntplib.NTPClient()
    try:
        # Query the NTP server
        response = client.request("pool.ntp.org", version=3)
        ntp_timestamp = float(response.tx_time)
    except (ntplib.NTPException, socket.error, OSError) as e:
        print(f"Error fetching NTP time: {e}", file=sys.stderr)
        ntp_timestamp = float(time())  # Fallback to system time

    # Convert the timestamp to a UTC datetime and format as 'YYYY-MM-DD'
    current_date = datetime.fromtimestamp(ntp_timestamp, timezone.utc)
    return current_date


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
        self._data: NestedConfig = {}# = self.load()
        self._units: UnitManagerProtocol = UnitManager()
        self._anchors: AnchorManagerProtocol = AnchorManager(self.units)
        self.load_units()
        self.populate_dynamic_anchors()
        self.load_anchors()

        self.resolver = ConfigResolver()
        self._load_hy_config()
    

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
            ")"
        ]

        with open(config_hy, 'w') as f:
            f.write('\n'.join(content))


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
        """
        Print the configuration in a formatted JSON style.

        Optionally filters the output to display the value of a specific key path.

        Parameters
        ----------
        filter_key : str, optional
            A dot-separated key path to filter the config output (e.g., 'gemini.api_key').
            If provided, only the value of the specified key will be printed. If the key
            points to a nested dictionary or list, its content is displayed in a
            formatted manner.

        Returns
        -------
        None

        Raises
        ------
        KeyError
            If the provided key path is invalid or does not exist in the configuration.
        """
        if filter_key:
            try:
                pretty_result = self.get_value(filter_key, pretty=True)
                print(pretty_result)
            except KeyError as e:
                print(f"Error: {e}")
        else:
            print(json.dumps(self.data, indent=4, sort_keys=True))


    def init_resources(self) -> None:
        """Copy resources to the user config directory if they do not already
        exist."""
        resources = ["system_prompt.txt", "config.json", "anchors.json", "units.json"]
        for item in resources:
            source_file = importlib.resources.files("utms.resources") / item
            destination_file = os.path.join(self.utms_dir, item)

            # Copy only if the destination file does not exist
            if not os.path.exists(destination_file):
                shutil.copy(str(source_file), destination_file)


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
                breakdowns = anchor.get("breakdowns")
                # Add anchor using the details loaded from the JSON
                anchor_config = AnchorConfig(
                    label=key,
                    name=name,
                    value=Decimal(timestamp),
                    groups=groups,
                    precision=Decimal(precision) if precision else None,
                    breakdowns=breakdowns,
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

    def load_units(self) -> None:
        """Loads time units from the 'units.json' file and populates the units
        dynamically.

        This method reads the `units.json` file, parses its content, and uses the `UnitManager`
        to add each unit to the configuration.
        """
        units_file = os.path.join(self.utms_dir, "units.json")

        if os.path.exists(units_file):
            with open(units_file, "r", encoding="utf-8") as f:
                units_data = json.load(f)

            # Iterate through the units data and add each unit
            for key, unit in units_data.items():
                name = unit.get("name")
                value = unit.get("value")
                # Add unit using the details loaded from the JSON
                self.units.add_unit(name, key, Decimal(value))

        else:
            print(f"Error: '{units_file}' not found.")

    def save_units(self) -> None:
        """Saves the current time units to the 'units.json' file.

        This method serializes the time units stored in the `self.units` instance
        and writes them to the `units.json` file.
        """
        units_file = os.path.join(self.utms_dir, "units.json")
        units_data = {}

        # Iterate through each unit and prepare data for saving
        for unit_abbreviation in self.units:
            unit = self.units[unit_abbreviation]
            units_data[unit_abbreviation] = {
                "name": unit.name,
                "symbol": unit_abbreviation,  # or another property if you have one
                "value": str(unit.value),
            }
        # Write the serialized units data to the file
        try:
            with open(units_file, "w", encoding="utf-8") as f:
                json.dump(units_data, f, ensure_ascii=False, indent=4)
            print(f"Units successfully saved to '{units_file}'")
        except (FileNotFoundError, PermissionError, OSError) as e:
            print(f"Error saving units: {e}")
        except json.JSONDecodeError as e:
            print(f"Error serializing data to JSON: {e}")

    def populate_dynamic_anchors(self) -> None:
        """Populates the `AnchorManager` instance with predefined datetime
        anchors.

        This method adds various datetime anchors such as Unix Time, CE Time, and Big Bang Time,
        using the `add_datetime_anchor` and `add_decimal_anchor` methods of the `AnchorManager`
        instance.  Each anchor is added with its name, symbol, and corresponding datetime value.
        """

        self.anchors.add_anchor(
            AnchorConfig(
                label="NT",
                name=f"Now Time ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})",
                value=get_ntp_date(),
                groups=["default", "dynamic", "modern"],
            )
        )
        self.anchors.add_anchor(
            AnchorConfig(
                label="DT",
                name=f"Day Time ({datetime.now().strftime('%Y-%m-%d 00:00:00')})",
                value=datetime(
                    datetime.now().year,
                    datetime.now().month,
                    datetime.now().day,
                    tzinfo=datetime.now().astimezone().tzinfo,
                ),
                breakdowns=[["dd", "cd", "s", "ms"], ["h", "m", "s", "ms"], ["KS", "s", "ms"]],
                groups=["dynamic", "modern"],
            )
        )
        self.anchors.add_anchor(
            AnchorConfig(
                label="MT",
                name=f"Month Time ({datetime.now().strftime('%Y-%m-01 00:00:00')})",
                value=datetime(
                    datetime.now().year,
                    datetime.now().month,
                    1,
                    tzinfo=datetime.now().astimezone().tzinfo,
                ),
                breakdowns=[
                    ["d", "dd", "cd", "s", "ms"],
                    ["w", "d", "dd", "cd", "s", "ms"],
                    ["MS", "KS", "s", "ms"],
                ],
                groups=["dynamic", "modern"],
            )
        )

        self.anchors.add_anchor(
            AnchorConfig(
                label="YT",
                name=f"Year Time ({datetime.now().strftime('%Y-01-01 00:00:00')})",
                value=datetime(
                    datetime.now().year, 1, 1, tzinfo=datetime.now().astimezone().tzinfo
                ),
                breakdowns=[
                    ["d", "dd", "cd", "s", "ms"],
                    ["w", "d", "dd", "cd", "s", "ms"],
                    ["M", "d", "dd", "cd", "s", "ms"],
                    ["MS", "KS", "s", "ms"],
                ],
                groups=["dynamic", "modern"],
            )
        )

    @property
    def utms_dir(self) -> str:
        return str(self._utms_dir)

    @property
    def data(self) -> ConfigData:
        return self._data

    @property
    def units(self) -> UnitManagerProtocol:
        return self._units

    @property
    def anchors(self) -> AnchorManagerProtocol:
        return self._anchors
