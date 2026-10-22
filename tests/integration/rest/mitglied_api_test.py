"""REST-Ablauf mit echtem PostgreSQL, Keycloak und Mailpit prüfen."""

from http import HTTPStatus
from os import getenv
from uuid import uuid4

import pytest
from common_api_test import keycloak_certificate_path, login, rest_url, timeout
from requests import delete, get, post, put, request

pytestmark = [
    pytest.mark.rest,
    pytest.mark.skipif(
        getenv("FITNESSSTUDIO_INTEGRATION") != "1",
        reason="Laufende Dienste erforderlich: FITNESSSTUDIO_INTEGRATION=1 setzen",
    ),
]


def test_admin_suche() -> None:
    response = get(
        rest_url, headers={"Authorization": f"Bearer {login()}"}, timeout=timeout
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json()["content"]


@pytest.mark.parametrize(
    ("username", "mitglied_id", "erwartet"),
    [
        ("admin", 20, HTTPStatus.OK),
        ("alice", 20, HTTPStatus.OK),
        ("alice", 30, HTTPStatus.FORBIDDEN),
        ("admin", 999999, HTTPStatus.NOT_FOUND),
    ],
)
def test_id_suche(username, mitglied_id, erwartet) -> None:
    response = get(
        f"{rest_url}/{mitglied_id}",
        headers={"Authorization": f"Bearer {login(username)}"},
        timeout=timeout,
    )
    assert response.status_code == erwartet


def test_query_suche() -> None:
    response = request(
        method="QUERY",
        url=f"{rest_url}/query",
        headers={"Authorization": f"Bearer {login()}"},
        json={"nachname": "Alpha", "page": 0, "size": 5},
        timeout=timeout,
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json()["content"][0]["email"] == "alice@fitnessstudio.de"


def test_anlegen_aendern_loeschen_und_mail() -> None:
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
        response = get(location, headers=admin_headers, timeout=timeout)
        assert response.status_code == HTTPStatus.OK
        mitglied_id = response.json()["id"]
        etag = response.headers["ETag"]
        response = get(
            location, headers={**admin_headers, "If-None-Match": etag}, timeout=timeout
        )
        assert response.status_code == HTTPStatus.NOT_MODIFIED

        update = {
            key: daten[key]
            for key in (
                "vorname",
                "nachname",
                "email",
                "geburtsdatum",
                "geschlecht",
                "interessen",
            )
        }
        update["vorname"] = "Geaendert"
        response = put(
            location,
            json=update,
            headers={**admin_headers, "If-Match": etag},
            timeout=timeout,
        )
        assert response.status_code == HTTPStatus.NO_CONTENT
        assert response.headers["ETag"] != etag
        response = put(
            location,
            json=update,
            headers={**admin_headers, "If-Match": etag},
            timeout=timeout,
        )
        assert response.status_code == HTTPStatus.PRECONDITION_FAILED

        mail = get("http://localhost:8025/api/v1/messages", timeout=timeout)
        assert mail.status_code == HTTPStatus.OK
        assert any(
            msg["Subject"] == f"Neues Mitglied: ID={mitglied_id}"
            for msg in mail.json()["messages"]
        )
        response = delete(location, headers=admin_headers, timeout=timeout)
        assert response.status_code == HTTPStatus.NO_CONTENT
        response = get(location, headers=admin_headers, timeout=timeout)
        assert response.status_code == HTTPStatus.NOT_FOUND
    finally:
        if location is not None:
            delete(location, headers=admin_headers, timeout=timeout)
        # Nur den eigens angelegten Testbenutzer entfernen, keine anderen Benutzer.
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
