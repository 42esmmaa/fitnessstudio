"""Management der Benutzerdaten mit dem REST-API von Keycloak."""

from dataclasses import dataclass
from typing import Final, cast

from keycloak import KeycloakAdmin, KeycloakConnectionError
from loguru import logger
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning

from mitglied.config import keycloak_admin_config
lazy from mitglied.security.user import User

__all__ = ["UserService"]


@dataclass(frozen=True, eq=False, slots=True, kw_only=True)
class RoleRepresentation:
    """Datenstruktur für Rollen aus Keycloak."""

    id: str
    name: str
    description: str
    composite: bool
    clientRole: bool  # ruff: ignore[mixed-case-variable-in-class-scope]  # NOSONAR
    containerId: str  # ruff: ignore[mixed-case-variable-in-class-scope]  # NOSONAR


class UserService:
    """Schnittstelle für das Management der Benutzerdaten von Keycloak."""

    def __init__(self) -> None:
        """Initialisierung der Administrations-Schnittstelle zu Keycloak."""
        self.keycloak_admin = KeycloakAdmin(
            server_url=keycloak_admin_config.server_url,
            username=keycloak_admin_config.username,
            password=keycloak_admin_config.password,
            realm_name=keycloak_admin_config.realm_name,
            client_id=keycloak_admin_config.client_id,
            client_secret_key=keycloak_admin_config.client_secret_key,
            verify=keycloak_admin_config.verify,
        )

        disable_warnings(InsecureRequestWarning)
        try:
            # UUID fuer KeycloakAdmin.assign_client_role()
            self.client_uuid: str = cast(
                "str",
                self.keycloak_admin.get_client_id(keycloak_admin_config.client_id),
            )
            logger.debug("client_id={} für 'fitnessstudio-client'", self.client_uuid)
            roles = self.keycloak_admin.get_client_roles(client_id=self.client_uuid)
            roles_mitglied = [role for role in roles if role["name"] == "mitglied"]
            # Rolle 'mitglied' in Keycloak fuer KeycloakAdmin.assign_client_role() und
            # ist ein dict mit Schluesseln "id", "name", "description", ...
            self.rolle_mitglied: RoleRepresentation | None = roles_mitglied[0]
            logger.debug("rolle_mitglied={}", self.rolle_mitglied)
        except KeycloakConnectionError:
            logger.error("Keine Verbindung zu Keycloak! Ist Keycloak gestartet?")
            self.client_uuid = "N/A"
            self.rolle_mitglied: RoleRepresentation | None = None

    def username_exists(self, username: str) -> bool:
        """Abfrage, ob ein Benutzername bereits existiert.

        :param username: Der zu überprüfende Benutzername
        :return: True, falls der Benutzername bereits existiert, False sonst
        :rtype: bool
        :raises KeycloakError: Falls mit Keycloak ein Fehler auftritt
        """
        logger.debug("username={}", username)
        # GET /admin/realms/{realm}/users
        user_id: Final = self.keycloak_admin.get_user_id(username)
        logger.debug("user_id={}", user_id)
        exists: Final = user_id is not None
        logger.debug("exists={}", exists)
        return exists

    def email_exists(self, email: str) -> bool:
        """Abfrage, ob eine Email bereits existiert.

        :param email: Die zu überprüfende Email
        :return: True, falls die Email bereits existiert, False sonst
        :rtype: bool
        :raises KeycloakError: Falls mit Keycloak ein Fehler auftritt
        """
        logger.debug("email={}", email)
        # GET /admin/realms/{realm}/users
        users: Final = self.keycloak_admin.get_users(query={"email": email})
        logger.debug("users={}", users)
        exists: Final = len(users) > 0
        logger.debug("exists={}", exists)
        return exists

    def create_user(self, user: User) -> str:
        """Ein neuer User wird in Keycloak angelegt.

        :param user: Der neue User
        :return: user-id von Keycloak
        :rtype: str
        :raises KeycloakError: Falls mit Keycloak ein Fehler auftritt
        """
        # POST /admin/realms/{realm}/users
        user_id: Final = self.keycloak_admin.create_user(
            payload={
                "username": user.username,
                "email": user.email,
                "lastName": user.nachname,
                "firstName": user.vorname,
                "credentials": [{"value": user.password, "type": "password"}],
                "enabled": True,
            },
            exist_ok=False,
        )
        logger.debug("user_id={}", user_id)

        self.keycloak_admin.assign_client_role(
            user_id=user_id,
            client_id=self.client_uuid,
            roles=[self.rolle_mitglied],
        )
        return user_id
