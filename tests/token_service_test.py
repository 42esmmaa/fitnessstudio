"""Token-Verarbeitung mit simuliertem Keycloak ohne laufenden Server prüfen."""

from unittest.mock import patch

import pytest
from jwcrypto.common import JWException
from keycloak import KeycloakAuthenticationError, KeycloakOperationError
from loguru import logger
from starlette.requests import Request

from mitglied.security import AuthorizationError, LoginError, Role, TokenService

BEARER_VALUE = "test-token"


@pytest.fixture
def service():
    """Keycloak-Client durch einen Mock ersetzen."""
    with patch("mitglied.security.token_service.KeycloakOpenID") as client:
        client.return_value.client_id = "fitnessstudio-client"
        yield TokenService()


@pytest.fixture
def claims():
    """Dekodierte Claims mit Client-Rollen bereitstellen."""
    return {
        "preferred_username": "alex",
        "email": "alex@example.org",
        "family_name": "Muster",
        "given_name": "Alex",
        "resource_access": {"fitnessstudio-client": {"roles": ["admin", "mitglied"]}},
    }


@pytest.mark.parametrize(
    ("username", "password"), [(None, "test"), ("alex", None), (None, None)]
)
def test_token_ohne_zugangsdaten(service, username, password) -> None:
    with pytest.raises(LoginError):
        service.token(username, password)
    service.keycloak.token.assert_not_called()


@pytest.mark.parametrize(
    "fehler", [KeycloakAuthenticationError, KeycloakOperationError]
)
def test_token_keycloak_fehler(service, fehler) -> None:
    service.keycloak.token.side_effect = fehler("Login abgelehnt")
    with pytest.raises(LoginError) as ausnahme:
        service.token("alex", "test")
    assert ausnahme.value.username == "alex"


def test_token_weitergabe_ohne_secret_im_log(service) -> None:
    antwort = {"access_token": "test-access-token", "expires_in": 300}
    service.keycloak.token.return_value = antwort
    nachrichten = []
    sink = logger.add(lambda message: nachrichten.append(str(message)))
    try:
        assert service.token("alex", "test-password") is antwort
    finally:
        logger.remove(sink)
    service.keycloak.token.assert_called_once_with("alex", "test-password")
    assert all("test-password" not in text for text in nachrichten)
    assert all("test-access-token" not in text for text in nachrichten)


def test_user_aus_token(service, claims) -> None:
    service.keycloak.decode_token.return_value = claims
    user = service.get_user_from_token("test-token")
    service.keycloak.decode_token.assert_called_once_with(token=BEARER_VALUE)
    assert user.username == "alex"
    assert user.email == "alex@example.org"
    assert user.nachname == "Muster"
    assert user.vorname == "Alex"
    assert user.roles == [Role.ADMIN, Role.MITGLIED]
    assert user.password is None


@pytest.mark.parametrize("feld", ["preferred_username", "email", "resource_access"])
def test_token_mit_fehlenden_claims(service, claims, feld) -> None:
    del claims[feld]
    service.keycloak.decode_token.return_value = claims
    with pytest.raises(AuthorizationError):
        service.get_user_from_token("test-token")


def test_token_mit_unbekannter_rolle(service, claims) -> None:
    claims["resource_access"]["fitnessstudio-client"]["roles"] = ["unbekannt"]
    service.keycloak.decode_token.return_value = claims
    with pytest.raises(AuthorizationError):
        service.get_user_from_token("test-token")


def test_token_mit_jwt_fehler(service) -> None:
    service.keycloak.decode_token.side_effect = JWException("Ungueltiger Token")
    with pytest.raises(AuthorizationError):
        service.get_user_from_token("test-token")


@pytest.mark.parametrize("header", [None, "", "Basic test", "Bearer", "Bearer a b"])
def test_request_ohne_gueltigen_bearer_header(service, header) -> None:
    headers = [] if header is None else [(b"authorization", header.encode())]
    request = Request({"type": "http", "headers": headers})
    with pytest.raises(AuthorizationError):
        service.get_user_from_request(request)
    service.keycloak.decode_token.assert_not_called()


def test_user_aus_request(service, claims) -> None:
    service.keycloak.decode_token.return_value = claims
    request = Request({
        "type": "http",
        "headers": [(b"authorization", b"bEaReR test-token")],
    })
    user = service.get_user_from_request(request)
    assert user.roles == [Role.ADMIN, Role.MITGLIED]
    service.keycloak.decode_token.assert_called_once_with(token=BEARER_VALUE)
