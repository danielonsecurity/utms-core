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
from utms.core.services.auth import AuthManager

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
            if f"VID:PID={vid}:{pid}" in port.hwid.upper():
                logger.info(f"Found matching device: {port.description} on {port.device}")
                return port.device
    return None


if __name__ == "__main__":
    config = Config()
    logger = get_logger()
    logger.info("--- UTMS Arduino Agent starting up ---")
    logger.info("Loading agent configuration...")
    try:
        agent_user = config.config.get_config('agent-user').value.value
        baud_rate = config.config.get_config('arduino-baud-rate').value.value
        api_base_url = config.config.get_config('api-base-url').value.value
        key_map_list = config.config.get_config('arduino-key-mapping').value.value
        ids_list = config.config.get_config('arduino-ids').value.value
        valid_hw_ids = list(ids_list.items())
        presence_away_confirmation_threshold_sec = config.config.get_config('arduino-presence-away-threshold').value.value
        logger.info(f"Server-side 'AWAY' confirmation threshold: {presence_away_confirmation_threshold_sec} seconds.")
        presence_present_confirmation_threshold_sec = config.config.get_config('arduino-presence-present-threshold').value.value
        logger.info(f"Server-side 'PRESENT' confirmation threshold: {presence_present_confirmation_threshold_sec} seconds.")
        logger.info(f"Loaded {len(key_map_list)} key mappings.")
        logger.info(f"Loaded {len(valid_hw_ids)} hardware IDs for scanning.")
        logger.info(f"Baud Rate: {baud_rate}, API URL: {api_base_url}")

    except (AttributeError, KeyError, TypeError) as e:
        logger.critical(f"❌ A critical configuration value is missing or malformed: {e}")
        logger.critical("   Please ensure 'arduino-baud-rate', 'api-base-url', 'arduino-key-mapping', and 'arduino-ids' are correctly set.")
        sys.exit(1)

    logger.info(f"Initializing authentication for user: '{agent_user}'")
    auth_manager = AuthManager(config, username=agent_user)
    
    serial_port = find_arduino_port(valid_hw_ids, logger)
    if not serial_port:
        logger.critical("❌ Could not find a connected Arduino device with the configured hardware IDs.")
        logger.critical("   Please ensure the Arduino is plugged in and the 'arduino-ids' config is correct.")
        sys.exit(1)

    PRESENCE_ENTITY_ID = "habit:system:Desk Presence"
    logger.info(f"Using '{PRESENCE_ENTITY_ID}' for presence tracking.")

    current_confirmed_presence_state: Optional[bool] = None 
    
    potential_away_start_time: Optional[float] = None 
    potential_present_start_time: Optional[float] = None 


    def handle_activity_toggle(entity_identifier: str, force_state: Optional[str] = None):
        logger.info(f"Handling event for: {entity_identifier} (Force state: {force_state})")
        
        try:
            entity_type, category, name = entity_identifier.split(':')
        except ValueError:
            logger.error(f"Invalid entity format: '{entity_identifier}'")
            return

        start_url = f"{api_base_url}/api/entities/{entity_type}/{category}/{name}/occurrences/start"
        end_url = f"{api_base_url}/api/entities/{entity_type}/{category}/{name}/occurrences/end"
        try:
            http_session = auth_manager.get_session()
        except RuntimeError as e:
            logger.error(f"Aborting action: Could not get authenticated session. Reason: {e}")
            return

        try:
            if force_state == 'start':
                response = http_session.post(start_url, timeout=5)
            elif force_state == 'end':
                end_payload = {"notes": "Automatic presence update.", "metadata": {}}
                response = http_session.post(end_url, json=end_payload, timeout=5)
            else: # Toggle
                response = http_session.post(start_url, timeout=5)
                if response.status_code == 409: # Toggling to END
                    logger.info(f"⚠️ '{name}' already running. Toggling to END.")
                    end_payload = {"notes": "", "metadata": {}}
                    end_response = http_session.post(end_url, json=end_payload, timeout=5)
                    if end_response.status_code == 200:
                        logger.info(f"✅ ENDED: '{name}' is now complete.")
                    else:
                        logger.error(f"❌ FAILED TO END '{name}'. API returned {end_response.status_code}: {end_response.text}")
                    return

            if response.status_code == 200:
                logger.info(f"✅ ACTION SUCCEEDED for '{name}'.")
            elif response.status_code == 409:
                logger.info(f"✅ STATE OK for '{name}'. No action was needed.")
            else:
                logger.error(f"❌ API Error for '{name}': {response.status_code} - {response.text}")

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Connection Error for '{name}': {e}")

    logger.info(f"Attempting to synchronize '{PRESENCE_ENTITY_ID}' to 'ended' state on startup...")
    handle_activity_toggle(PRESENCE_ENTITY_ID, force_state='end')
    current_confirmed_presence_state = False 
    while True:
        try:
            with serial.Serial(serial_port, baud_rate, timeout=1) as ser:
                logger.info(f"✅ Agent online. Listening to Arduino on {serial_port}...")
                while True:
                    current_time = time.monotonic()
                    if potential_away_start_time is not None and \
                       current_confirmed_presence_state is not False: 
                        if (current_time - potential_away_start_time) >= presence_away_confirmation_threshold_sec:
                            logger.info(f"✅ Confirmed AWAY: User has been away for > {presence_away_confirmation_threshold_sec}s.")
                            handle_activity_toggle(PRESENCE_ENTITY_ID, force_state='end')
                            current_confirmed_presence_state = False
                            potential_away_start_time = None 
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
                    if not line_bytes: 
                        continue       

                    line = line_bytes.decode("utf-8", errors="ignore").strip()
                    if not line: 
                        continue

                    logger.debug(f"SERIAL_RX: {line}")
                    if line.startswith("KEY_COMMAND"):
                        command_sequence = line.replace("KEY_COMMAND_", "").strip() 
                        logger.info(f"Received command sequence: '{command_sequence}'")
                        entity_id = key_map_list.get(command_sequence)
                        if entity_id:
                            handle_activity_toggle(entity_id)
                        else:
                            logger.warning(f"Received command '{command_sequence}' but no action is mapped in config.")
                        if presence_present_confirmation_threshold_sec > 0: 
                            logger.info("Keypad activity: Immediately confirming PRESENT due to user interaction.")
                            if current_confirmed_presence_state is not True:
                                handle_activity_toggle(PRESENCE_ENTITY_ID, force_state='start')
                                current_confirmed_presence_state = True
                        potential_present_start_time = None 
                        potential_away_start_time = None    

                    elif line == "PRESENCE_PRESENT":
                        logger.info("🧑‍💻 Arduino reports: User is PRESENT.")
                        potential_away_start_time = None 

                        if current_confirmed_presence_state is not True:
                            if presence_present_confirmation_threshold_sec > 0:
                                if potential_present_start_time is None: 
                                    logger.info(f"Potential PRESENT detected. Starting {presence_present_confirmation_threshold_sec}s confirmation timer.")
                                    potential_present_start_time = current_time 
                                
                            else: 
                                logger.info("Updating UTMS to PRESENT (no present threshold).")
                                handle_activity_toggle(PRESENCE_ENTITY_ID, force_state='start')
                                current_confirmed_presence_state = True
                        else:
                            logger.debug("Already confirmed PRESENT, no change needed for UTMS.")
                            
                            
                            potential_present_start_time = None


                    elif line == "PRESENCE_AWAY":
                        logger.info("🚶 Arduino reports: User is AWAY.")
                        potential_present_start_time = None 

                        if current_confirmed_presence_state is True or current_confirmed_presence_state is None:
                            if presence_away_confirmation_threshold_sec > 0:
                                if potential_away_start_time is None: 
                                    logger.info(f"Potential AWAY detected. Starting {presence_away_confirmation_threshold_sec}s confirmation timer.")
                                    potential_away_start_time = current_time 
                                
                            else: 
                                logger.info("Updating UTMS to AWAY (no away threshold).")
                                handle_activity_toggle(PRESENCE_ENTITY_ID, force_state='end')
                                current_confirmed_presence_state = False
                        else:
                            logger.debug("Already confirmed AWAY, no change needed for UTMS.")
                            
                            potential_away_start_time = None

        except serial.SerialException as e:
            logger.error(f"❌ Serial port error on {serial_port}: {e}")
            logger.error("   Device may have been disconnected. Rescanning in 10 seconds...")
            time.sleep(10)
            serial_port = find_arduino_port(valid_hw_ids, logger)
            if not serial_port:
                logger.error("Could not re-find the Arduino. Will retry scanning in 10s.")

        except KeyboardInterrupt:
            logger.info("\n🛑 Agent stopped by user.")
            sys.exit(0)
        except Exception as e:
            logger.critical(f"An unexpected critical error occurred: {e}", exc_info=True)
            time.sleep(10)

