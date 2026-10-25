"""GraphQL mit simulierten Services und echten Strawberry-Requests prüfen."""

from datetime import date
from importlib import import_module
from unittest.mock import create_autospec

import pytest
from fastapi.testclient import TestClient

from mitglied import app
from mitglied.entity import Geschlecht, Tarif
from mitglied.repository import Slice
from mitglied.security import AuthorizationError, Role, TokenService, User
from mitglied.service import (
    ForbiddenError,
    MitgliedDTO,
    MitgliedService,
    MitgliedWriteService,
    NotFoundError,
)

graphql = import_module("mitglied.graphql_api.schema")
MITGLIED_ID = 1000
CREATE = "mutation($input: MitgliedInput!) { create(mitgliedInput: $input) { id } }"


@pytest.fixture
def services(monkeypatch):
    """Datenbank und Keycloak durch kontrollierte Services ersetzen."""
    dto = MitgliedDTO(
        id=1000,
        version=1,
        vorname="Alex",
        nachname="Muster",
        email="alex@example.org",
        geburtsdatum=date(2000, 1, 1),
        geschlecht=Geschlecht.DIVERS,
        vertrag=None,
        interessen=None,
    )
    read = create_autospec(MitgliedService, instance=True)
    read.find_by_id.return_value = dto
    read.find.return_value = Slice(content=(dto,), total_elements=1)
    token = create_autospec(TokenService, instance=True)
    user = User(
        username="admin",
        email="admin@example.org",
        vorname="Admin",
        nachname="Muster",
        roles=[Role.ADMIN],
    )
    token.get_user_from_request.return_value = user
    token.get_user_from_token.return_value = user
    token.token.return_value = {"access_token": "test-token", "expires_in": 300}
    write = create_autospec(MitgliedWriteService, instance=True)
    write.create.return_value = dto
    monkeypatch.setattr(graphql, "_service", read)
    monkeypatch.setattr(graphql, "_token_service", token)
    monkeypatch.setattr(graphql, "get_user_service", lambda: None)
    monkeypatch.setattr(graphql, "MitgliedWriteService", lambda **_kwargs: write)
    return read, token, write


@pytest.fixture
def client():
    """GraphQL-Router ohne Lifespan und Datenbankinitialisierung bereitstellen."""
    http_client = TestClient(app)
    try:
        yield http_client
    finally:
        http_client.close()


def test_mitglied_mit_optionalen_feldern(client, services):
    response = client.post(
        "/graphql",
        json={
            "query": (
                '{ mitglied(mitgliedId: "1000") {'
                " id geschlecht interessen vertrag { tarif } } }"
            ),
        },
    )
    assert response.json() == {
        "data": {
            "mitglied": {
                "id": 1000,
                "geschlecht": "DIVERS",
                "interessen": None,
                "vertrag": None,
            }
        }
    }
    assert services[0].find_by_id.call_args.kwargs["mitglied_id"] == MITGLIED_ID


def test_suche_ohne_begrenzung_auf_fuenf(client, services):
    daten = client.post(
        "/graphql",
        json={
            "query": '{ mitglieder(suchparameter: {nachname: "Mus"}) { id } }',
        },
    ).json()
    assert daten == {"data": {"mitglieder": [{"id": 1000}]}}
    argumente = services[0].find.call_args.kwargs
    assert argumente["suchparameter"].nachname == "Mus"
    assert argumente["pageable"].size == 0


def test_suche_nur_fuer_admin(client, services):
    services[1].get_user_from_request.return_value = User(
        username="alex",
        email="alex@example.org",
        vorname="Alex",
        nachname="Muster",
        roles=[Role.MITGLIED],
    )
    daten = client.post(
        "/graphql", json={"query": "{ mitglieder(suchparameter: null) { id } }"}
    ).json()
    assert daten == {"data": {"mitglieder": []}}
    services[0].find.assert_not_called()


def test_fehlendes_mitglied(client, services):
    services[0].find_by_id.side_effect = NotFoundError(mitglied_id=1000)
    daten = client.post(
        "/graphql", json={"query": '{ mitglied(mitgliedId: "1000") { id } }'}
    ).json()
    assert daten == {"data": {"mitglied": None}}


@pytest.mark.parametrize("fehler", [AuthorizationError, ForbiddenError])
def test_geschuetzte_einzelsuche(client, services, fehler):
    if fehler is AuthorizationError:
        services[1].get_user_from_request.side_effect = fehler
    else:
        services[0].find_by_id.side_effect = fehler
    daten = client.post(
        "/graphql", json={"query": '{ mitglied(mitgliedId: "1000") { id } }'}
    ).json()
    assert daten["data"]["mitglied"] is None
    assert daten["errors"]


@pytest.fixture
def eingabe():
    """JSON-Variablen für eine Neuanlage vorbereiten."""
    return {
        "vorname": "Alex",
        "nachname": "Muster",
        "email": "neu@example.org",
        "geburtsdatum": "2000-01-01",
        "geschlecht": "DIVERS",
        "zahlungen": [],
    }


def test_anlegen_ohne_interessen_und_vertrag(client, services, eingabe):
    daten = client.post(
        "/graphql",
        json={
            "query": CREATE,
            "variables": {"input": eingabe},
        },
    ).json()
    assert daten == {"data": {"create": {"id": 1000}}}
    mitglied = services[2].create.call_args.kwargs["mitglied"]
    assert mitglied.interessen is None
    assert mitglied.vertrag is None
    assert mitglied.geschlecht is Geschlecht.DIVERS


def test_anlegen_mit_vertrag_und_zahlung(client, services, eingabe):
    eingabe["vertrag"] = {
        "beginn": "2026-10-01",
        "monatlicherBeitrag": "29.90",
        "tarif": "STUDENT",
        "getraenkeflat": True,
    }
    eingabe["zahlungen"] = [{"betrag": "29.90", "zahlungsdatum": "2026-10-01"}]
    eingabe["interessen"] = ["Yoga"]
    daten = client.post(
        "/graphql",
        json={
            "query": CREATE,
            "variables": {"input": eingabe},
        },
    ).json()
    assert "errors" not in daten
    mitglied = services[2].create.call_args.kwargs["mitglied"]
    assert mitglied.vertrag.tarif is Tarif.STUDENT
    assert len(mitglied.zahlungen) == 1
    assert mitglied.interessen == ["Yoga"]


def test_ungueltige_email_wird_vor_speichern_abgelehnt(client, services, eingabe):
    eingabe["email"] = "keine-email"
    daten = client.post(
        "/graphql",
        json={
            "query": CREATE,
            "variables": {"input": eingabe},
        },
    ).json()
    assert daten["errors"]
    services[2].create.assert_not_called()


def test_login_mit_tatsaechlicher_tokenlaufzeit(client, services):
    daten = client.post(
        "/graphql",
        json={
            "query": (
                'mutation { login(username: "admin", password: "test") {'
                " token expiresIn roles } }"
            ),
        },
    ).json()
    assert daten == {
        "data": {
            "login": {
                "token": "test-token",
                "expiresIn": "300",
                "roles": ["ADMIN"],
            }
        }
    }
    services[1].token.assert_called_once()
    assert services[1].token.call_args.kwargs == {
        "username": "admin",
        "password": "test",
    }
