import requests
import time
import os
from typing import Optional

from utms.core.config import UTMSConfig
from utms.core.mixins import LoggerMixin

class AuthManager(LoggerMixin):
    """
    Manages M2M authentication by storing, reading, and using refresh tokens
    to provide authenticated HTTP sessions.
    """
    CREDENTIALS_FILENAME = ".credentials"

    def __init__(self, config: UTMSConfig, username: str):
        if not username:
            raise ValueError("AuthManager must be initialized for a specific user.")
            
        self.config = config
        self.username = username
        self.enabled = False
        
        self.token_url: Optional[str] = None
        self.client_id: Optional[str] = None
        self.refresh_token: Optional[str] = None
        
        self.access_token: Optional[str] = None
        self.token_expires_at: float = 0
        
        self.session = requests.Session()
        
        self._load_config_and_token()

    def _load_config_and_token(self):
        """Loads required OIDC client settings and the user's refresh token."""
        try:
            self.enabled = self.config.config.get_config('agent-auth-enabled').value.value
            if not self.enabled:
                self.logger.warning("Authentication is disabled in global config.")
                return

            auth_url = self.config.config.get_config('oidc-auth-url').value.value
            realm = self.config.config.get_config('oidc-realm').value.value
            self.client_id = self.config.config.get_config('oidc-client-id').value.value
            self.token_url = f"{auth_url}/realms/{realm}/protocol/openid-connect/token"
            
            credentials_path = os.path.join(self.config.utms_dir, "users", self.username, self.CREDENTIALS_FILENAME)
            with open(credentials_path, 'r') as f:
                self.refresh_token = f.read().strip()
            
            if not self.refresh_token:
                self.logger.error(f"Credentials file is empty: {credentials_path}")
                self.enabled = False

        except FileNotFoundError:
            self.logger.error(f"Credentials file not found for user '{self.username}' at {credentials_path}")
            self.logger.error("Please run 'utms auth login' to authenticate.")
            self.enabled = False
        except (AttributeError, KeyError) as e:
            self.logger.error(f"Auth config value is missing from global.hy: {e}. Disabling authentication.")
            self.enabled = False

    def _refresh_access_token(self):
        """Uses the refresh token to get a new access token."""
        if not self.enabled or not self.refresh_token:
            raise RuntimeError("Cannot refresh token: authentication is disabled or refresh token is missing.")
        
        self.logger.info(f"Attempting to refresh access token for user '{self.username}'...")
        payload = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "refresh_token": self.refresh_token,
        }

        try:
            response = requests.post(self.token_url, data=payload)
            response.raise_for_status()
            data = response.json()
            
            self.access_token = data["access_token"]
            self.token_expires_at = time.time() + data.get("expires_in", 300) - 30 
            self.session.headers.update({"Authorization": f"Bearer {self.access_token}"})
            self.logger.info("✅ Successfully refreshed access token.")
        except requests.exceptions.RequestException as e:
            self.logger.critical(f"❌ CRITICAL: Failed to refresh token: {e}")
            if e.response:
                self.logger.critical(f"   Response: {e.response.text}")
                if e.response.status_code in [400, 401]:
                     self.logger.critical("   The refresh token may be invalid or revoked. Please run 'utms auth login' again.")
            self.access_token = None
            raise RuntimeError("Could not refresh access token.") from e

    def get_session(self) -> requests.Session:
        """
        Returns a requests.Session object with a valid Authorization header.
        Refreshes the token automatically if it's expired.
        """
        if not self.enabled:
            self.logger.debug("Auth disabled, returning plain requests session.")
            return requests.Session()
        
        if not self.access_token or time.time() >= self.token_expires_at:
            self._refresh_access_token()
            
        return self.session
