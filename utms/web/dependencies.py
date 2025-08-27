import requests
from functools import lru_cache
from typing import Dict, Optional

from fastapi import Depends, Request, HTTPException
from jose import jwt, JWTError


from utms.core.config.config import UTMSConfig

from utms.web.api.models.user import CurrentUser

@lru_cache()
def get_config() -> UTMSConfig:
    """Returns the singleton instance of the UTMS Core."""
    return UTMSConfig()

@lru_cache()
def get_oidc_public_keys(jwks_uri: str) -> Dict:
    """Retrieves and caches the OIDC provider's public keys from the given URI."""
    try:
        response = requests.get(jwks_uri)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Could not connect to OIDC provider: {e}")


async def get_optional_current_user(
    request: Request,
    config: UTMSConfig = Depends(get_config) 
) -> Optional[CurrentUser]:
    """
    Tries to authenticate from the Authorization header. Returns a CurrentUser if
    a valid token is found, otherwise returns None. Does not block the request.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    token = parts[1]
    try:
        jwks_uri = config.config.get_config("oidc-jwks-uri").get_value()
        algorithm = config.config.get_config("oidc-algorithm").get_value()
        audience = config.config.get_config("oidc-audience").get_value()
    except AttributeError:
        config.logger.error("OIDC settings are missing from global config.hy. Cannot validate tokens.")
        return None
    try:
        jwks = get_oidc_public_keys(jwks_uri)
        payload = jwt.decode(
            token,
            jwks,
            algorithms=[algorithm],
            audience=audience,
        )

        user_id = payload.get("sub")
        if not user_id:
            return None

        client_access = payload.get("resource_access", {}).get(audience, {})
        roles = client_access.get("roles", [])

        return CurrentUser(id=user_id, roles=roles)

    except JWTError:
        return None
