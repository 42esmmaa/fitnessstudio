"""Keycloak-Benutzeranlage mit simuliertem Admin-Client prüfen."""

from unittest.mock import patch

import pytest
from keycloak import KeycloakConnectionError, KeycloakError

from mitglied.config import keycloak_admin_config
from mitglied.security import User, UserService


@pytest.fixture
def admin_client():
    """Admin-Client ohne Verbindung zu Keycloak bereitstellen."""
    with patch("mitglied.security.user_service.KeycloakAdmin") as factory:
        client = factory.return_value
        client.get_client_id.return_value = "client-uuid"
        client.get_client_roles.return_value = [
            {"id": "admin-role", "name": "admin"},
            {"id": "mitglied-role", "name": "mitglied"},
        ]
        yield client


def test_user_service_verwendet_client_und_mitgliedrolle(admin_client) -> None:
    service = UserService()
    admin_client.get_client_id.assert_called_once_with(keycloak_admin_config.client_id)
    admin_client.get_client_roles.assert_called_once_with(client_id="client-uuid")
    assert service.client_uuid == "client-uuid"
    assert service.rolle_mitglied == {"id": "mitglied-role", "name": "mitglied"}


@pytest.mark.parametrize("user_id", [None, "user-uuid"])
def test_username_exists(admin_client, user_id) -> None:
    admin_client.get_user_id.return_value = user_id
    service = UserService()
    assert service.username_exists("alex") is (user_id is not None)
    admin_client.get_user_id.assert_called_once_with("alex")


@pytest.mark.parametrize("users", [[], [{"id": "user-uuid"}]])
def test_email_exists(admin_client, users) -> None:
    admin_client.get_users.return_value = users
    service = UserService()
    assert service.email_exists("alex@example.org") is bool(users)
    admin_client.get_users.assert_called_once_with(query={"email": "alex@example.org"})


def test_create_user_payload_und_rollenzuweisung(admin_client) -> None:
    admin_client.create_user.return_value = "user-uuid"
    service = UserService()
    user = User(
        username="alex",
        email="alex@example.org",
        nachname="Muster",
        vorname="Alex",
        roles=[],
        password=None,
    )
    assert service.create_user(user) == "user-uuid"
    admin_client.create_user.assert_called_once_with(
        payload={
            "username": "alex",
            "email": "alex@example.org",
            "lastName": "Muster",
            "firstName": "Alex",
            "credentials": [{"value": None, "type": "password"}],
            "enabled": True,
        },
        exist_ok=False,
    )
    admin_client.assign_client_role.assert_called_once_with(
        user_id="user-uuid",
        client_id="client-uuid",
        roles=[{"id": "mitglied-role", "name": "mitglied"}],
    )


def test_create_user_fehler_ohne_rollenzuweisung(admin_client) -> None:
    admin_client.create_user.side_effect = KeycloakError("Testfehler")
    service = UserService()
    user = User(
        username="alex",
        email="alex@example.org",
        nachname="Muster",
        vorname="Alex",
        roles=[],
    )
    with pytest.raises(KeycloakError):
        service.create_user(user)
    admin_client.assign_client_role.assert_not_called()


def test_fehlende_keycloak_verbindung(admin_client) -> None:
    admin_client.get_client_id.side_effect = KeycloakConnectionError("Testfehler")
    service = UserService()
    assert service.client_uuid == "N/A"
    assert service.rolle_mitglied is None
