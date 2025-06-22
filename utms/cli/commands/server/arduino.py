import serial
import requests
import time
import sys
import subprocess
from typing import Dict, Optional, List, Tuple, Any
import serial.tools.list_ports

from utms.utils import list_to_dict
from utms import UTMSConfig as Config
from utms.core.logger import get_logger
from ..core import Command, CommandManager


def _parse_flat_list_to_tuples(flat_list: List[Any]) -> List[Tuple[str, str]]:
    """
    Parses a flat list of [key, value, key, value, ...] into a list of tuples.
    Used for loading the VID/PID pairs.
    """
    if not isinstance(flat_list, list):
        return []

    tuples = []
    for i in range(0, len(flat_list), 2):
        if i + 1 < len(flat_list):
            tuples.append((str(flat_list[i]), str(flat_list[i+1])))
    return tuples


def find_arduino_port(valid_ids: List[Tuple[str, str]], logger) -> Optional[str]:
    """
    Scans available serial ports and identifies the Arduino using a list of
    valid hardware ID tuples (VID, PID).
    """
    if not valid_ids:
        logger.warning("No valid hardware IDs provided for Arduino scan.")
        return None

    ports = serial.tools.list_ports.comports()
    logger.debug(f"Scanning {len(ports)} available ports for matching hardware IDs...")
    for port in ports:
        for vid, pid in valid_ids:
            # Check for the pattern 'VID:PID=xxxx:xxxx' in the hardware ID string
            if f"VID:PID={vid}:{pid}" in port.hwid.upper():
                logger.info(f"Found matching device: {port.description} on {port.device}")
                return port.device
    return None


def handle_arduino_listener(args, config: Config) -> None:
    """
    Handles the 'server arduino' command by starting a long-running daemon.
    """
    logger = get_logger('arduino_agent')
    logger.info("--- UTMS Arduino Agent starting up ---")

    # --- Load All Configuration ---
    logger.info("Loading agent configuration...")
    try:
        # Simple values
        baud_rate = config.config.get_config('arduino-baud-rate').value.value
        api_base_url = config.config.get_config('api-base-url').value.value
        notification_executable = config.config.get_config('notification-executable').value.value

        # Complex mappings
        key_map_list = config.config.get_config('arduino-key-mapping').value.value['value']
        key_to_entity_map = list_to_dict(key_map_list)

        ids_list = config.config.get_config('arduino-ids').value.value['value']
        valid_hw_ids = _parse_flat_list_to_tuples(ids_list)

        presence_away_confirmation_threshold_sec = config.config.get_config('arduino-presence-away-threshold').value.value
        logger.info(f"Server-side 'AWAY' confirmation threshold: {presence_away_confirmation_threshold_sec} seconds.")

        presence_present_confirmation_threshold_sec = config.config.get_config('arduino-presence-present-threshold').value.value
        logger.info(f"Server-side 'PRESENT' confirmation threshold: {presence_present_confirmation_threshold_sec} seconds.")

        logger.info(f"Loaded {len(key_to_entity_map)} key mappings.")
        logger.info(f"Loaded {len(valid_hw_ids)} hardware IDs for scanning.")
        logger.info(f"Baud Rate: {baud_rate}, API URL: {api_base_url}, Notifier: '{notification_executable}'")

    except (AttributeError, KeyError, TypeError) as e:
        logger.critical(f"❌ A critical configuration value is missing or malformed: {e}")
        logger.critical("   Please ensure 'arduino-baud-rate', 'api-base-url', 'notification-executable', 'arduino-key-mapping', and 'arduino-ids' are correctly set.")
        sys.exit(1)

    # --- Auto-detect Serial Port using Configured IDs ---
    serial_port = find_arduino_port(valid_hw_ids, logger)
    if not serial_port:
        logger.critical("❌ Could not find a connected Arduino device with the configured hardware IDs.")
        logger.critical("   Please ensure the Arduino is plugged in and the 'arduino-ids' config is correct.")
        sys.exit(1)

    PRESENCE_ENTITY_ID = "habit:system:Desk Presence"
    logger.info(f"Using '{PRESENCE_ENTITY_ID}' for presence tracking.")

    current_confirmed_presence_state: Optional[bool] = None 
    # Timestamp when Arduino first reported potential AWAY state
    potential_away_start_time: Optional[float] = None 
    potential_present_start_time: Optional[float] = None 

    # --- Helper Functions using Configured Values ---
    def _send_notification(title: str, message: str = ""):
        """Sends a desktop notification using the configured executable."""
        command = [notification_executable, title]
        if message:
            command.append(message)
        try:
            subprocess.run(command, check=False)
        except FileNotFoundError:
            logger.warning(f"Notification command '{notification_executable}' not found. Skipping notification.")
        except Exception as ex:
            logger.error(f"Failed to send notification: {ex}")

    def handle_activity_toggle(entity_identifier: str, force_state: Optional[str] = None):
        """
        Handles toggling an activity OR forcing it into a specific state.
        """
        logger.info(f"Handling event for: {entity_identifier} (Force state: {force_state})")
        
        parts = entity_identifier.split(':')
        if len(parts) != 3:
            logger.error(f"Invalid entity format: '{entity_identifier}'")
            return

        entity_type, category, name = parts
        
        start_url = f"{api_base_url}/api/entities/{entity_type}/{category}/{name}/occurrences/start"
        end_url = f"{api_base_url}/api/entities/{entity_type}/{category}/{name}/occurrences/end"
        
        action_taken = False

        if force_state == 'start':
            logger.debug(f"Forcing START for {name} at {start_url}")
            try:
                response = requests.post(start_url, timeout=5)
                if response.status_code == 200:
                    logger.info(f"✅ FORCED START: '{name}' is now active.")
                    _send_notification(f"✅ {name}", "Desk presence started.")
                    action_taken = True
                elif response.status_code == 409: # Already started
                    logger.info(f"✅ Already started: '{name}' was already active. No action needed.")
                    action_taken = True # Considered action taken as state is correct
                else:
                    logger.error(f"❌ API Error on forced start for {name}: {response.status_code} - {response.text}")
            except requests.exceptions.RequestException as e:
                logger.error(f"❌ Connection Error on forced start for {name}: {e}")
        
        elif force_state == 'end':
            logger.debug(f"Forcing END for {name} at {end_url}")
            end_payload = {"notes": "Automatic presence update.", "metadata": {}}
            try:
                response = requests.post(end_url, json=end_payload, timeout=5)
                if response.status_code == 200:
                    logger.info(f"✅ FORCED END: '{name}' is now complete.")
                    _send_notification(f"🛑 {name}", "Desk presence ended.")
                    action_taken = True
                elif response.status_code == 409: # No active occurrence to end
                    logger.info(f"✅ Already ended: '{name}' was not active. No action needed.")
                    action_taken = True # Considered action taken as state is correct
                else:
                    logger.error(f"❌ API Error on forced end for {name}: {response.status_code} - {response.text}")
            except requests.exceptions.RequestException as e:
                logger.error(f"❌ Connection Error on forced end for {name}: {e}")

        else: # Default toggle behavior (for keypad keys)
            logger.debug(f"Toggling {name}. Attempting START at {start_url}")
            _send_notification("UTMS Activity", f"Toggling: {name}")
            try:
                response = requests.post(start_url, timeout=5)
                if response.status_code == 200:
                    logger.info(f"✅ STARTED: '{name}' is now active.")
                    _send_notification(f"✅ {name} Started", "Activity tracked.")
                    action_taken = True
                elif response.status_code == 409:
                    logger.info(f"⚠️ '{name}' already running. Toggling to END.")
                    end_payload = {"notes": "", "metadata": {}} # Keypad presses don't have notes
                    end_response = requests.post(end_url, json=end_payload, timeout=5)
                    if end_response.status_code == 200:
                         logger.info(f"✅ ENDED: '{name}' is now complete.")
                         _send_notification(f"🛑 {name} Stopped", "Activity no longer tracked.")
                         action_taken = True
                    else:
                        logger.error(f"❌ FAILED TO END '{name}'. API returned {end_response.status_code}: {end_response.text}")
                else:
                    logger.error(f"❌ API Error on start attempt for {name}: {response.status_code} - {response.text}")
            except requests.exceptions.RequestException as e:
                 logger.error(f"❌ Connection Error on toggle for {name}: {e}")


    logger.info(f"Attempting to synchronize '{PRESENCE_ENTITY_ID}' to 'ended' state on startup...")
    handle_activity_toggle(PRESENCE_ENTITY_ID, force_state='end')
    current_confirmed_presence_state = False # Assume away after sync

    # --- Main Listening Loop ---
    while True:
        try:
            with serial.Serial(serial_port, baud_rate, timeout=1) as ser:
                logger.info(f"✅ Agent online. Listening to Arduino on {serial_port}...")
                _send_notification("UTMS Arduino Agent", "Listener is online and connected.")
                while True:
                    current_time = time.monotonic()
                    if potential_away_start_time is not None and \
                       current_confirmed_presence_state is not False: # Only if not already confirmed away
                        if (current_time - potential_away_start_time) >= presence_away_confirmation_threshold_sec:
                            logger.info(f"✅ Confirmed AWAY: User has been away for > {presence_away_confirmation_threshold_sec}s.")
                            handle_activity_toggle(PRESENCE_ENTITY_ID, force_state='end')
                            current_confirmed_presence_state = False
                            potential_away_start_time = None # Reset timer
                            potential_present_start_time = None

                    if potential_present_start_time is not None and \
                       current_confirmed_presence_state is not True:
                        if (current_time - potential_present_start_time) >= presence_present_confirmation_threshold_sec:
                            logger.info(f"✅ Confirmed PRESENT: User has been present for > {presence_present_confirmation_threshold_sec}s.")
                            handle_activity_toggle(PRESENCE_ENTITY_ID, force_state='start')
                            current_confirmed_presence_state = True
                            potential_present_start_time = None
                            potential_away_start_time = None 

                    line_bytes = ser.readline()
                    if not line_bytes: # Timeout, no data from Arduino
                        continue       # Go back to check potential_away_start_time

                    line = line_bytes.decode("utf-8", errors="ignore").strip()
                    if not line: # Empty line after decode
                        continue

                    logger.debug(f"SERIAL_RX: {line}")
                    if line.startswith("KEY_COMMAND"):
                        command_sequence = line.replace("KEY_COMMAND_", "").strip() 
                        logger.info(f"Received command sequence: '{command_sequence}'")
                        entity_id = key_to_entity_map.get(command_sequence)
                        if entity_id:
                            handle_activity_toggle(entity_id)
                        else:
                            logger.warning(f"Received command '{command_sequence}' but no action is mapped in config.")
                        if presence_present_confirmation_threshold_sec > 0: # Only if debouncing PRESENT
                            logger.info("Keypad activity: Immediately confirming PRESENT due to user interaction.")
                            if current_confirmed_presence_state is not True:
                                handle_activity_toggle(PRESENCE_ENTITY_ID, force_state='start')
                                current_confirmed_presence_state = True
                        potential_present_start_time = None # Clear any pending present confirmation timer
                        potential_away_start_time = None    # Clear any pending away confirmation timer

                    elif line == "PRESENCE_PRESENT":
                        logger.info("🧑‍💻 Arduino reports: User is PRESENT.")
                        potential_away_start_time = None # Arduino says present, so cancel pending away confirmation

                        if current_confirmed_presence_state is not True:
                            if presence_present_confirmation_threshold_sec > 0:
                                if potential_present_start_time is None: # Start timer only if not already started
                                    logger.info(f"Potential PRESENT detected. Starting {presence_present_confirmation_threshold_sec}s confirmation timer.")
                                    potential_present_start_time = current_time # Use the loop's current_time
                                # Else: timer is already running, let it continue
                            else: # No PRESENT threshold, act immediately
                                logger.info("Updating UTMS to PRESENT (no present threshold).")
                                handle_activity_toggle(PRESENCE_ENTITY_ID, force_state='start')
                                current_confirmed_presence_state = True
                        else:
                            logger.debug("Already confirmed PRESENT, no change needed for UTMS.")
                            # If already confirmed PRESENT, ensure any potential_present_start_time is cleared
                            # as Arduino is re-confirming.
                            potential_present_start_time = None


                    elif line == "PRESENCE_AWAY":
                        logger.info("🚶 Arduino reports: User is AWAY.")
                        potential_present_start_time = None # Arduino says away, so cancel pending present confirmation

                        if current_confirmed_presence_state is True or current_confirmed_presence_state is None:
                            if presence_away_confirmation_threshold_sec > 0:
                                if potential_away_start_time is None: # Start timer only if not already started
                                    logger.info(f"Potential AWAY detected. Starting {presence_away_confirmation_threshold_sec}s confirmation timer.")
                                    potential_away_start_time = current_time # Use the loop's current_time
                                # Else: timer is already running, let it continue
                            else: # No AWAY threshold, act immediately
                                logger.info("Updating UTMS to AWAY (no away threshold).")
                                handle_activity_toggle(PRESENCE_ENTITY_ID, force_state='end')
                                current_confirmed_presence_state = False
                        else:
                            logger.debug("Already confirmed AWAY, no change needed for UTMS.")
                            # If already confirmed AWAY, ensure any potential_away_start_time is cleared.
                            potential_away_start_time = None

        except serial.SerialException as e:
            logger.error(f"❌ Serial port error on {serial_port}: {e}")
            logger.error("   Device may have been disconnected. Rescanning in 10 seconds...")
            _send_notification("UTMS Arduino Agent Error", f"Disconnected from {serial_port}")
            time.sleep(10)
            # Rescan for the port in case it was reconnected on a different name
            serial_port = find_arduino_port(valid_hw_ids, logger)
            if not serial_port:
                logger.error("Could not re-find the Arduino. Will retry scanning in 10s.")

        except KeyboardInterrupt:
            logger.info("\n🛑 Agent stopped by user.")
            _send_notification("UTMS Arduino Agent", "Listener is now offline.")
            sys.exit(0)
        except Exception as e:
            logger.critical(f"An unexpected critical error occurred: {e}", exc_info=True)
            time.sleep(10)


def register_server_command(command_manager: CommandManager) -> None:
    # (This function remains unchanged)
    command = Command(
        "server", "arduino", lambda args: handle_arduino_listener(args, command_manager.config), is_default=False
    )
    command.set_help("Run the Arduino hardware listener daemon.")
    command.set_description(
        "Starts a long-running process that listens for events from a connected Arduino "
        "and triggers corresponding actions via the API, based on system configuration."
    )
    command_manager.register_command(command)
