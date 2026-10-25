"""Fixtures für REST-Integrationstests gegen den laufenden Appserver."""

from http import HTTPStatus
from os import getenv
from uuid import uuid4

import pytest
from common_api_test import keycloak_certificate_path, login, rest_url, timeout
from requests import delete, get, post


@pytest.fixture(autouse=True)
def laufende_dienste() -> None:
    """Integrationstests nur bei ausdrücklich aktivierten Diensten ausführen."""
    if getenv("FITNESSSTUDIO_INTEGRATION") != "1":
        pytest.skip("Laufende Dienste erforderlich: FITNESSSTUDIO_INTEGRATION=1 setzen")


@pytest.fixture
def neues_mitglied():
    """Eigenes Testmitglied anlegen und anschließend mit Keycloak-User entfernen."""
    admin_headers = {"Authorization": f"Bearer {login()}"}
    email = f"integration-{uuid4().hex}@example.org"
    daten = {
        "vorname": "Integration",
        "nachname": "Test",
        "email": email,
        "geburtsdatum": "2000-01-01",
        "geschlecht": "D",
        "interessen": ["Yoga"],
        "vertrag": {
            "beginn": "2026-10-01",
            "monatlicher_beitrag": "29.90",
            "tarif": "STUDENT",
            "getraenkeflat": True,
        },
        "zahlungen": [{"betrag": "29.90", "zahlungsdatum": "2026-10-01"}],
    }
    location = None
    try:
        response = post(rest_url, json=daten, timeout=timeout)
        assert response.status_code == HTTPStatus.CREATED
        location = response.headers["Location"]
        yield response, daten, admin_headers
    finally:
        if location is not None:
            response = delete(location, headers=admin_headers, timeout=timeout)
            response.raise_for_status()
        # Ausschließlich den eigens angelegten Testbenutzer entfernen.
        users_url = "https://localhost:8843/admin/realms/fitnessstudio/users"
        response = get(
            users_url,
            params={"username": email, "exact": "true"},
            headers=admin_headers,
            timeout=timeout,
            verify=keycloak_certificate_path,
        )
        response.raise_for_status()
        for user in response.json():
            assert user["username"] == email
            response = delete(
                f"{users_url}/{user['id']}",
                headers=admin_headers,
                timeout=timeout,
                verify=keycloak_certificate_path,
            )
            response.raise_for_status()
