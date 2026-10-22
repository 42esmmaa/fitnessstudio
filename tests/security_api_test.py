"""Login und Rollenprüfung ohne laufenden Keycloak-Server prüfen."""

from http import HTTPStatus
from unittest.mock import create_autospec

import pytest
from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient

from mitglied import app
from mitglied.fastapi_app import authorization_error_handler
from mitglied.security import (
    AuthorizationError,
    LoginError,
    Role,
    RolesRequired,
    TokenService,
    User,
)
from mitglied.security.dependencies import get_token_service


@pytest.fixture
def user() -> User:
    """Testbenutzer ohne Passwort bereitstellen."""
    return User(
        username="alex",
        email="alex@example.org",
        vorname="Alex",
        nachname="Muster",
        roles=[Role.MITGLIED],
    )


@pytest.fixture
def service():
    """TokenService durch einen Mock ersetzen."""
    return create_autospec(TokenService, instance=True)


@pytest.fixture
def client(service):
    """Anwendung ohne Lifespan und damit ohne DB-Neubefüllung testen."""
    vorherige_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_token_service] = lambda: service
    http_client = TestClient(app)
    try:
        yield http_client
    finally:
        http_client.close()
        app.dependency_overrides.clear()
        app.dependency_overrides.update(vorherige_overrides)


def test_query_token_erfolgreich(client, service, user) -> None:
    login_daten = {"username": "alex", "password": "test"}
    service.token.return_value = {
        "access_token": "test-access-token",
        "refresh_token": "test-refresh-token",
        "expires_in": 300,
    }
    service.get_user_from_token.return_value = user
    response = client.request("QUERY", "/auth/token", json=login_daten)
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        "token": "test-access-token",
        "expires_in": 300,
        "rollen": ["MITGLIED"],
    }
    service.token.assert_called_once_with(**login_daten)


@pytest.mark.parametrize(
    "inhalt",
    [
        "",
        "{",
        "null",
        "[]",
        "42",
        "{}",
        '{"username":"alex"}',
        '{"username":"alex","password":null}',
        '{"username":[],"password":"test"}',
        '{"username":"alex","password":"test","extra":true}',
    ],
)
def test_query_token_fehlerhafter_body(client, service, inhalt) -> None:
    response = client.request(
        "QUERY",
        "/auth/token",
        content=inhalt,
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    service.token.assert_not_called()


def test_query_token_falsche_zugangsdaten(client, service) -> None:
    service.token.side_effect = LoginError("alex")
    response = client.request(
        "QUERY", "/auth/token", json={"username": "alex", "password": "test"}
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["title"] == "Unauthorized"


def test_query_token_nicht_verifizierbar(client, service) -> None:
    service.token.return_value = {
        "access_token": "test-access-token",
        "expires_in": 300,
    }
    service.get_user_from_token.side_effect = AuthorizationError
    response = client.request(
        "QUERY", "/auth/token", json={"username": "alex", "password": "test"}
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.parametrize(
    ("required", "erwartet"),
    [
        (Role.MITGLIED, HTTPStatus.OK),
        ([Role.ADMIN, Role.MITGLIED], HTTPStatus.OK),
        (Role.ADMIN, HTTPStatus.FORBIDDEN),
        ([Role.ADMIN], HTTPStatus.FORBIDDEN),
        ([], HTTPStatus.FORBIDDEN),
    ],
)
def test_roles_required(required, erwartet, service, user) -> None:
    test_app = FastAPI()
    test_app.dependency_overrides[get_token_service] = lambda: service
    service.get_user_from_request.return_value = user

    @test_app.get("/geschuetzt", dependencies=[Depends(RolesRequired(required))])
    def geschuetzt(request: Request) -> dict[str, str]:
        return {"username": request.state.current_user.username}

    with TestClient(test_app) as http_client:
        response = http_client.get("/geschuetzt")
    assert response.status_code == erwartet
    if erwartet == HTTPStatus.OK:
        assert response.json() == {"username": "alex"}


def test_roles_required_ungueltiger_token(service) -> None:
    test_app = FastAPI()
    test_app.dependency_overrides[get_token_service] = lambda: service
    test_app.exception_handler(AuthorizationError)(authorization_error_handler)
    service.get_user_from_request.side_effect = AuthorizationError

    @test_app.get("/geschuetzt", dependencies=[Depends(RolesRequired(Role.ADMIN))])
    def geschuetzt() -> dict[str, str]:
        return {"status": "ok"}

    with TestClient(test_app) as http_client:
        response = http_client.get("/geschuetzt")
    assert response.status_code == HTTPStatus.UNAUTHORIZED
