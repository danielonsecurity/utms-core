import argparse
from utms import UTMSConfig
from utms.cli.commands.core import Command, CommandManager
from utms.cli.commands.server.utils import get_service_status, SERVICES

def handle_status(args: argparse.Namespace, config: UTMSConfig):
    """
    Handler for the 'utms server status' command.
    """
    print(f"{'SERVICE':<12} {'STATUS':<25} {'PID':<10}")
    print("-" * 50)
    
    services_to_check = args.services
    if "all" in services_to_check:
        services_to_check = sorted(list(SERVICES.keys()))

    for service_name in services_to_check:
        if service_name not in SERVICES:
            # Silently skip unknown services for status check
            continue
        
        status, pid = get_service_status(config, service_name)
        pid_str = str(pid) if pid > 0 else "-"
        
        print(f"{service_name:<12} {status:<25} {pid_str:<10}")

def register_server_status_command(command_manager: CommandManager):
    """
    Registers the 'server status' command.
    """
    status_cmd = Command(
        "server",
        "status",
        lambda args: handle_status(args, command_manager.config)
    )
    
    status_cmd.set_help("Show the status of UTMS services.")
    
    status_cmd.set_description(
        "Displays the current running status and Process ID (PID) of each UTMS service."
    )
    
    # We can reuse the services argument, but we'll define it here
    # since it's slightly different (no 'action' context in the help text).
    status_cmd.add_argument(
        "services",
        nargs='*',
        default=["all"],
        help=f"The service(s) to check. Choices: {list(SERVICES.keys())}. Defaults to 'all'."
    )
    
    command_manager.register_command(status_cmd)
