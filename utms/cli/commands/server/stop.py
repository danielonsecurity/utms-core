import argparse
from utms import UTMSConfig
from utms.cli.commands.core import Command, CommandManager
from utms.cli.commands.server.utils import stop_service, SERVICES
from utms.cli.commands.server.helper import add_services_argument
from utms.core.logger import get_logger

logger = get_logger()

def handle_stop(args: argparse.Namespace, config: UTMSConfig):
    """
    Handler for the 'utms server stop' command.
    """
    services_to_stop = args.services
    if "all" in services_to_stop:
        services_to_stop = list(SERVICES.keys())

    for service_name in services_to_stop:
        if service_name not in SERVICES:
            logger.warning(f"Unknown service '{service_name}'. Skipping.")
            continue
        
        stop_service(config, service_name)

def register_server_stop_command(command_manager: CommandManager):
    """
    Registers the 'server stop' command.
    """
    stop_cmd = Command(
        "server",
        "stop",
        lambda args: handle_stop(args, command_manager.config)
    )
    
    stop_cmd.set_help("Stop one or more running UTMS services.")
    
    stop_cmd.set_description(
        """Stops the specified UTMS services that are running in the background.
        
Use 'all' to stop all running services.
If no services are specified, 'all' is assumed.

Example:
  utms server stop agent
"""
    )
    
    # Use the helper function to add the 'services' argument
    add_services_argument(stop_cmd, action="stop")
    
    command_manager.register_command(stop_cmd)
