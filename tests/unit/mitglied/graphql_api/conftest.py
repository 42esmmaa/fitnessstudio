"""Fixtures für GraphQL-Unit-Tests mit simulierten Services."""

from datetime import date
from importlib import import_module
from unittest.mock import Mock, create_autospec

import pytest
from fastapi.testclient import TestClient

from mitglied import app
from mitglied.entity import Geschlecht
from mitglied.repository import Slice
from mitglied.security import Role, TokenService, User
from mitglied.service import (
    MitgliedDTO,
    MitgliedService,
    MitgliedWriteService,
)

graphql = import_module("mitglied.graphql_api.schema")


@pytest.fixture
def mail(monkeypatch) -> Mock:
    """Keinen echten Mailversand in Unit-Tests: send_mail durch einen Mock ersetzen."""
    mock = Mock()
    monkeypatch.setattr(graphql, "send_mail", mock)
    return mock


@pytest.fixture
def services(monkeypatch, mail):  # ruff: ignore[unused-function-argument]
    """Datenbank und Keycloak durch kontrollierte Services ersetzen."""
    # "mail" als Parameter, damit der Mailversand immer simuliert wird
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
