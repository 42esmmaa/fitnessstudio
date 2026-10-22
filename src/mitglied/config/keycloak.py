"""Konfiguration für _python-keycloak_ zum Zugriff auf _Keycloak_."""

from dataclasses import dataclass, field
from typing import Final

from mitglied.config.config import app_config

__all__ = ["keycloak_config"]


@dataclass(frozen=True, eq=False, slots=True)
class KeycloakConfig:
    """Allgemeine Konfigurationsdaten für Keycloak."""

    server_url: str
    realm_name: str
    client_id: str
    client_secret_key: str = field(repr=False)
    verify: bool = False


_keycloak_toml: Final = app_config.get("keycloak", {})

_schema: Final = _keycloak_toml.get("schema", "https")
_host: Final[str] = _keycloak_toml.get("host", "keycloak")
_port: Final[int] = _keycloak_toml.get("port", 8443)
_url: Final = f"{_schema}://{_host}:{_port}/"

_realm: Final[str] = _keycloak_toml.get("realm", "fitnessstudio")
_client_id: Final[str] = _keycloak_toml.get("client-id", "fitnessstudio-client")
_client_secret: Final[str] = _keycloak_toml.get("client-secret", "")

keycloak_config = KeycloakConfig(
    server_url=_url,
    realm_name=_realm,
    client_id=_client_id,
    client_secret_key=_client_secret,
    verify=False,
)
"""Schnittstelle zu Keycloak durch _python-keycloak_."""
