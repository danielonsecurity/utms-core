import argparse
import webbrowser
import http.server
import socketserver
import os
from urllib.parse import urlparse, parse_qs
import requests

from utms import UTMSConfig
from utms.cli.commands.core import Command, CommandManager
from utms.core.logger import get_logger

logger = get_logger()

def handle_login(args: argparse.Namespace, config: UTMSConfig):
    """
    Handler for the 'utms auth login' command.
    """
    username = args.user
    logger.info(f"Starting interactive login for user: {username}")
    
    try:
        keycloak_url = config.config.get_config('oidc-auth-url').value.value
        realm = config.config.get_config('oidc-realm').value.value
        client_id = config.config.get_config('oidc-client-id').value.value
    except (AttributeError, KeyError):
        logger.error("Error: One or more required keys ('oidc-auth-url', 'oidc-realm', 'oidc-client-id') are not defined in your global config.hy.")
        return

    redirect_port = 8989
    redirect_uri = f"http://localhost:{redirect_port}"

    auth_url = (
        f"{keycloak_url}/realms/{realm}/protocol/openid-connect/auth"
        f"?client_id={client_id}"
        f"&response_type=code"
        f"&redirect_uri={redirect_uri}"
        f"&scope=openid+offline_access"
    )

    print("Opening your browser to log in...")
    webbrowser.open(auth_url)

    auth_code = None

    class CodeHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            nonlocal auth_code
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            if "code" in query_params:
                auth_code = query_params["code"][0]
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"<html><body><h1>Success!</h1><p>You can close this browser tab.</p></body></html>")
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Error: Could not find code in redirect.")

    with socketserver.TCPServer(("", redirect_port), CodeHandler) as httpd:
        print(f"Waiting for Keycloak to redirect to http://localhost:{redirect_port}...")
        httpd.handle_request()

    if not auth_code:
        logger.error("Error: Did not receive an authorization code from Keycloak.")
        return

    print("Authorization code received. Exchanging for tokens...")
    token_url = f"{keycloak_url}/realms/{realm}/protocol/openid-connect/token"
    payload = {
        "client_id": client_id,
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": redirect_uri,
    }
    try:
        client_secret_config = config.config.get_config('oidc-client-secret')
        payload['client_secret'] = client_secret_config.value.value
        logger.debug("Client secret found in config. Adding to token exchange request.")
    except (AttributeError, KeyError):
        logger.debug("No client secret found in config. Proceeding without it.")

    response = requests.post(token_url, data=payload)
    if response.status_code != 200:
        logger.error(f"Error exchanging code for token: {response.text}")
        return

    refresh_token = response.json().get("refresh_token")
    if not refresh_token:
        logger.error("Error: Login succeeded, but no refresh_token was returned.")
        logger.error("Ensure 'offline_access' is an assigned optional scope for your client in Keycloak.")
        return

    user_dir = os.path.join(config.utms_dir, "users", username)
    os.makedirs(user_dir, exist_ok=True)
    credentials_path = os.path.join(user_dir, ".credentials")
    
    with open(credentials_path, 'w') as f:
        f.write(refresh_token)
    
    logger.info(f"✅ Success! Refresh token saved for user '{username}' to: {credentials_path}")


def register_auth_login_command(command_manager: CommandManager):
    """
    Registers the 'auth login' command.
    """
    login_cmd = Command(
        "auth",
        "login",
        lambda args: handle_login(args, command_manager.config)
    )
    
    login_cmd.set_help("Perform an interactive browser login to retrieve and save agent credentials.")
    login_cmd.set_description(
        """Opens a web browser to log into your identity provider.
        
Upon successful login (including OTP), this command retrieves a long-lived
refresh token and saves it securely in the specified user's configuration
directory. This token is then used by UTMS agents (like the Arduino listener)
to authenticate non-interactively.
"""
    )
    
    # Add the required --user argument
    login_cmd.add_argument(
        "-u", "--user",
        required=True,
        help="The UTMS username for whom to store the credentials (e.g., 'daniel')."
    )
    
    command_manager.register_command(login_cmd)
