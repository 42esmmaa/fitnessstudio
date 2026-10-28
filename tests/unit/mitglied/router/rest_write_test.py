"""REST-Endpunkte zum Ändern und Löschen mit simulierten Services prüfen."""

from http import HTTPStatus
from unittest.mock import create_autospec, patch

import pytest
from fastapi.testclient import TestClient

from mitglied import app
from mitglied.router.dependencies import get_write_service
from mitglied.security import AuthorizationError, Role, TokenService, User
from mitglied.security.dependencies import get_token_service
from mitglied.service import (
    EmailExistsError,
    ForbiddenError,
    MitgliedWriteService,
    NotFoundError,
    VersionOutdatedError,
)

MITGLIED_ID = 1000


@pytest.fixture
def daten():
    """Gültige Eingabedaten für einen PUT-Request."""
    return {
        "vorname": "Alex",
        "nachname": "Muster",
        "email": "alex@example.org",
        "geburtsdatum": "2000-01-01",
        "geschlecht": "D",
    }


@pytest.fixture
def service():
    """Schreibservice durch einen Mock ersetzen."""
    mock = create_autospec(MitgliedWriteService, instance=True)
    mock.update.return_value.version = 2
    return mock


@pytest.fixture
def token_service():
    """TokenService mit einem administrativen Benutzer simulieren."""
    mock = create_autospec(TokenService, instance=True)
    mock.get_user_from_request.return_value = User(
        username="admin",
        email="admin@example.org",
        vorname="Admin",
        nachname="Muster",
        roles=[Role.ADMIN],
    )
    return mock


@pytest.fixture
def client(service, token_service):
    """Anwendung ohne Lifespan und Datenbank-Neubefüllung testen."""
    vorherige_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_write_service] = lambda: service
    app.dependency_overrides[get_token_service] = lambda: token_service
    http_client = TestClient(app)
    try:
        yield http_client
    finally:
        http_client.close()
        app.dependency_overrides.clear()
        app.dependency_overrides.update(vorherige_overrides)


def test_post_anlegen_location_und_hintergrundmail(
    client, service, token_service, daten
) -> None:
    daten["zahlungen"] = []
    service.create.return_value.id = MITGLIED_ID
    with patch("mitglied.router.mitglied_write_router.send_mail") as mail:
        response = client.post("/rest", json=daten)
        mail.assert_called_once_with(service.create.return_value)
    assert response.status_code == HTTPStatus.CREATED
    assert response.headers["location"] == f"http://testserver/rest/{MITGLIED_ID}"
    assert response.content == b""
    service.create.assert_called_once()
    mitglied = service.create.call_args.kwargs["mitglied"]
    assert mitglied.email == "alex@example.org"
    assert mitglied.vertrag is None
    assert mitglied.zahlungen == []
    token_service.get_user_from_request.assert_not_called()


def test_post_email_bereits_vergeben(client, service, daten) -> None:
    daten["zahlungen"] = []
    service.create.side_effect = EmailExistsError("alex@example.org")
    with patch("mitglied.router.mitglied_write_router.send_mail") as mail:
        response = client.post("/rest", json=daten)
        mail.assert_not_called()
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response.headers["content-type"] == "application/problem+json"


def test_post_validierungsfehler(client, service, daten) -> None:
    daten["zahlungen"] = []
    daten["email"] = "keine-email"
    with patch("mitglied.router.mitglied_write_router.send_mail") as mail:
        response = client.post("/rest", json=daten)
        mail.assert_not_called()
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    service.create.assert_not_called()


@pytest.mark.parametrize("rolle", [Role.ADMIN, Role.MITGLIED])
def test_put_erfolgreich(client, service, token_service, daten, rolle) -> None:
    token_service.get_user_from_request.return_value.roles[:] = [rolle]
    response = client.put("/rest/1000", json=daten, headers={"If-Match": '"1"'})
    assert response.status_code == HTTPStatus.NO_CONTENT
    assert response.content == b""
    assert response.headers["etag"] == '"2"'
    service.update.assert_called_once()
    argumente = service.update.call_args.kwargs
    assert argumente["mitglied_id"] == MITGLIED_ID
    assert argumente["version"] == 1
    assert argumente["mitglied"].email == "alex@example.org"
    # der User aus dem Token wird fuer die Eigentuemerpruefung durchgereicht
    assert argumente["user"] is token_service.get_user_from_request.return_value


@pytest.mark.parametrize(
    ("if_match", "erwartet"),
    [
        (None, HTTPStatus.PRECONDITION_REQUIRED),
        ("1", HTTPStatus.PRECONDITION_FAILED),
        ('""', HTTPStatus.PRECONDITION_FAILED),
        ('"ungueltig"', HTTPStatus.PRECONDITION_FAILED),
        ('W/"1"', HTTPStatus.PRECONDITION_FAILED),
    ],
)
def test_put_ohne_gueltigen_if_match(
    client, service, daten, if_match, erwartet
) -> None:
    headers = {} if if_match is None else {"If-Match": if_match}
    response = client.put("/rest/1000", json=daten, headers=headers)
    assert response.status_code == erwartet
    assert response.headers["content-type"] == "application/problem+json"
    service.update.assert_not_called()


@pytest.mark.parametrize(
    ("fehler", "erwartet"),
    [
        (NotFoundError(), HTTPStatus.NOT_FOUND),
        (EmailExistsError("alex@example.org"), HTTPStatus.UNPROCESSABLE_ENTITY),
        (VersionOutdatedError(1), HTTPStatus.PRECONDITION_FAILED),
        (ForbiddenError(), HTTPStatus.FORBIDDEN),
    ],
)
def test_put_service_fehler(client, service, daten, fehler, erwartet) -> None:
    service.update.side_effect = fehler
    response = client.put("/rest/1000", json=daten, headers={"If-Match": '"1"'})
    assert response.status_code == erwartet
    assert response.headers["content-type"] == "application/problem+json"


def test_put_ungueltige_daten(client, service, daten) -> None:
    daten["email"] = "keine-email"
    response = client.put("/rest/1000", json=daten, headers={"If-Match": '"1"'})
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    service.update.assert_not_called()


@pytest.mark.parametrize("rolle", [Role.ADMIN, Role.MITGLIED])
def test_delete_erfolgreich(client, service, token_service, rolle) -> None:
    token_service.get_user_from_request.return_value.roles[:] = [rolle]
    response = client.delete("/rest/1000")
    assert response.status_code == HTTPStatus.NO_CONTENT
    assert response.content == b""
    service.delete_by_id.assert_called_once_with(
        mitglied_id=1000, user=token_service.get_user_from_request.return_value
    )


def test_delete_fremdes_mitglied_verboten(client, service, token_service) -> None:
    token_service.get_user_from_request.return_value.roles[:] = [Role.MITGLIED]
    service.delete_by_id.side_effect = ForbiddenError
    response = client.delete("/rest/1000")
    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.headers["content-type"] == "application/problem+json"


@pytest.mark.parametrize("methode", ["PUT", "DELETE"])
def test_schreiben_ohne_rolle(client, service, token_service, daten, methode) -> None:
    token_service.get_user_from_request.return_value.roles.clear()
    response = client.request(
        methode, "/rest/1000", json=daten, headers={"If-Match": '"1"'}
    )
    assert response.status_code == HTTPStatus.FORBIDDEN
    service.update.assert_not_called()
    service.delete_by_id.assert_not_called()


@pytest.mark.parametrize("methode", ["PUT", "DELETE"])
def test_schreiben_ohne_token(client, service, token_service, daten, methode) -> None:
    token_service.get_user_from_request.side_effect = AuthorizationError
    response = client.request(
        methode, "/rest/1000", json=daten, headers={"If-Match": '"1"'}
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    service.update.assert_not_called()
    service.delete_by_id.assert_not_called()
