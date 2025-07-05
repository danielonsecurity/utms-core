import argparse
from utms import UTMSConfig
from utms.cli.commands.core import Command, CommandManager
from utms.cli.commands.server.utils import start_service, SERVICES
from utms.cli.commands.server.helper import add_services_argument, add_foreground_argument
from utms.core.logger import get_logger

logger = get_logger()

def handle_start(args: argparse.Namespace, config: UTMSConfig):
    """
    Handler for the 'utms server start' command.
    """
    services_to_start = args.services
    if "all" in services_to_start:
        services_to_start = list(SERVICES.keys())
    
    if args.foreground and len(services_to_start) > 1:
        logger.error("Cannot start multiple services in foreground mode. Please specify one service.")
        return

    for service_name in services_to_start:
        if service_name not in SERVICES:
            logger.warning(f"Unknown service '{service_name}'. Skipping.")
            continue
            
        start_service(config, service_name, foreground=args.foreground)

def register_server_start_command(command_manager: CommandManager):
    """
    Registers the 'server start' command.
    """
    start_cmd = Command(
        "server",
        "start",
        lambda args: handle_start(args, command_manager.config)
    )
    
    start_cmd.set_help("Start one or more UTMS services (api, agent, arduino, etc.).")
    
    start_cmd.set_description(
        """Starts the specified UTMS services as background processes.
        
Use 'all' to start all available services.
If no services are specified, 'all' is assumed.

Example:
  utms server start api agent
  utms server start -f api  (runs the API in the foreground)
"""
    )
    
    # Use the helper functions to add arguments
    add_services_argument(start_cmd, action="start")
    add_foreground_argument(start_cmd)
    
    command_manager.register_command(start_cmd)
