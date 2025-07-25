import argparse
import requests
import sys

from utms import UTMSConfig as Config
from ..core import Command, CommandManager
from .helper import add_entity_identifier_argument

# Define your API's base URL. This should ideally come from your config.
API_BASE_URL = "http://127.0.0.1:8000"

def handle_start_command(args: argparse.Namespace, config: Config) -> None:
    """
    Handles the 'start' command by calling the UTMS API to start an occurrence.

    This function parses the entity identifier, constructs the appropriate API
    endpoint URL, and sends a POST request to start the entity's occurrence.
    It provides user-friendly feedback based on the API's response.
    """
    identifier = args.entity_identifier
    parts = identifier.split(':')

    if len(parts) != 3:
        print(f"Error: Invalid format for entity identifier '{identifier}'.")
        print("Please use the format: 'entity_type:category:name'")
        sys.exit(1)

    entity_type, category, name = parts
    
    # Construct the API URL
    url = f"{API_BASE_URL}/api/entities/{entity_type}/{category}/{name}/occurrences/start"
    print(f"▶️  Attempting to start: {identifier}...")

    try:
        response = requests.post(url)

        # Handle the API response
        if response.status_code == 200:
            # Success
            data = response.json()
            start_time = data.get('attributes', {}).get('active-occurrence-start-time', {}).get('value', 'N/A')
            print(f"✅ Success! Occurrence started at {start_time}.")
        elif response.status_code == 404:
            # Entity not found
            print(f"❌ Error: Entity '{identifier}' not found.")
            sys.exit(1)
        elif response.status_code == 409:
            # Occurrence already in progress (Conflict)
            print(f"⚠️  Warning: An occurrence for '{identifier}' is already in progress.")
        else:
            # Other server-side errors
            print(f"❌ Error: Received an unexpected response from the server (Status {response.status_code}).")
            print(f"   Response: {response.text}")
            sys.exit(1)

    except requests.exceptions.RequestException as e:
        print(f"❌ Error: Could not connect to the UTMS API at {API_BASE_URL}.")
        print(f"   Please ensure the UTMS web server is running.")
        sys.exit(1)


def register_start_command(command_manager: CommandManager) -> None:
    """
    Registers the 'start' command with the given command manager.
    """
    command = Command(
        "activity",
        "start",
        lambda args: handle_start_command(args, command_manager.config),
        is_default=False,
    )
    command.set_help("Start a new occurrence for a specific entity.")
    command.set_description(
        "Takes an entity identifier (e.g., 'habit:sleep:Sleep') and calls the API "
        "to begin a new timed occurrence for it."
    )
    
    # Add the required argument using the helper
    add_entity_identifier_argument(command)

    command_manager.register_command(command)
