from utms.cli.commands.core import Command
from utms.cli.commands.server.utils import SERVICES

def add_services_argument(command: Command, action: str):
    """Adds the 'services' argument to a server subcommand."""
    command.add_argument(
        "services",
        nargs='*',
        default=["all"],
        help=f"The service(s) to {action}. Choices: {list(SERVICES.keys())}. Defaults to 'all'."
    )

def add_foreground_argument(command: Command):
    """Adds the '--foreground' argument."""
    command.add_argument(
        "-f", "--foreground",
        action="store_true",
        help="Run a single specified service in the foreground, attached to the console."
    )
