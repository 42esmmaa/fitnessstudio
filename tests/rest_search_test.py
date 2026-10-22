"""Geschützte REST-Suche mit simulierten Services prüfen."""

from datetime import date
from decimal import Decimal
from http import HTTPStatus
from unittest.mock import create_autospec

import pytest
from fastapi.testclient import TestClient

from mitglied import app
from mitglied.entity import Geschlecht, Tarif
from mitglied.repository import Slice
from mitglied.router.dependencies import get_service
from mitglied.security import AuthorizationError, Role, TokenService, User
from mitglied.security.dependencies import get_token_service
from mitglied.service import MitgliedDTO, MitgliedService, NotFoundError, VertragDTO


@pytest.fixture
def service():
    """Suchservice mit einer vorbereiteten Ergebnisseite bereitstellen."""
    mock = create_autospec(MitgliedService, instance=True)
    mock.find.return_value = Slice(
        content=(
            MitgliedDTO(
                id=1000,
                version=1,
                vorname="Alex",
                nachname="Muster",
                email="alex@example.org",
                geburtsdatum=date(2000, 1, 1),
                geschlecht=Geschlecht.DIVERS,
                interessen=None,
                vertrag=VertragDTO(
                    beginn=date(2026, 10, 1),
                    monatlicher_beitrag=Decimal("29.90"),
                    tarif=Tarif.STUDENT,
                    getraenkeflat=True,
                ),
            ),
        ),
        total_elements=13,
    )
    return mock


@pytest.fixture
def token_service():
    """Administrativen Benutzer für die Rollenprüfung bereitstellen."""
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
    """Anwendung ohne Lifespan und PostgreSQL-Zugriff prüfen."""
    vorherige_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_service] = lambda: service
    app.dependency_overrides[get_token_service] = lambda: token_service
    http_client = TestClient(app)
    try:
        yield http_client
    finally:
        http_client.close()
        app.dependency_overrides.clear()
        app.dependency_overrides.update(vorherige_overrides)


@pytest.mark.parametrize("methode", ["GET", "QUERY"])
def test_suche_mit_seitenmetadaten(client, service, methode) -> None:
    parameter = {"nachname": "Mus", "page": 1, "size": 5}
    response = (
        client.get("/rest", params=parameter)
        if methode == "GET"
        else client.request("QUERY", "/rest/query", json=parameter)
    )
    assert response.status_code == HTTPStatus.OK
    daten = response.json()
    assert daten["page"] == {
        "size": 5,
        "number": 1,
        "total_elements": 13,
        "total_pages": 3,
    }
    mitglied = daten["content"][0]
    assert mitglied["geschlecht"] == "D"
    assert mitglied["geburtsdatum"] == "2000-01-01"
    assert mitglied["interessen"] is None
    assert mitglied["vertrag"]["tarif"] == "STUDENT"
    assert Decimal(mitglied["vertrag"]["monatlicher_beitrag"]) == Decimal("29.90")
    service.find.assert_called_once()
    argumente = service.find.call_args.kwargs
    assert argumente["suchparameter"].nachname == "Mus"
    assert (argumente["pageable"].number, argumente["pageable"].size) == (1, 5)


def test_query_email_und_size_null(client, service) -> None:
    response = client.request(
        "QUERY", "/rest/query", json={"email": "alex@example.org", "size": 0}
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json()["page"]["total_pages"] == 1
    assert service.find.call_args.kwargs["suchparameter"].email == "alex@example.org"


@pytest.mark.parametrize("methode", ["GET", "QUERY"])
@pytest.mark.parametrize("parameter", [{"page": -1}, {"size": 101}, {"falsch": "x"}])
def test_suche_ungueltige_parameter(client, service, methode, parameter) -> None:
    response = (
        client.get("/rest", params=parameter)
        if methode == "GET"
        else client.request("QUERY", "/rest/query", json=parameter)
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    service.find.assert_not_called()


@pytest.mark.parametrize("methode", ["GET", "QUERY"])
def test_suche_ohne_treffer(client, service, methode) -> None:
    service.find.side_effect = NotFoundError()
    response = (
        client.get("/rest")
        if methode == "GET"
        else client.request("QUERY", "/rest/query", json={})
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.headers["content-type"] == "application/problem+json"


@pytest.mark.parametrize("methode", ["GET", "QUERY"])
def test_suche_ohne_adminrolle(client, service, token_service, methode) -> None:
    token_service.get_user_from_request.return_value = User(
        username="alex",
        email="alex@example.org",
        vorname="Alex",
        nachname="Muster",
        roles=[Role.MITGLIED],
    )
    response = (
        client.get("/rest")
        if methode == "GET"
        else client.request("QUERY", "/rest/query", json={})
    )
    assert response.status_code == HTTPStatus.FORBIDDEN
    service.find.assert_not_called()


@pytest.mark.parametrize("methode", ["GET", "QUERY"])
def test_suche_ohne_gueltigen_token(client, service, token_service, methode) -> None:
    token_service.get_user_from_request.side_effect = AuthorizationError
    response = (
        client.get("/rest")
        if methode == "GET"
        else client.request("QUERY", "/rest/query", json={})
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    service.find.assert_not_called()
