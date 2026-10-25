"""POST-Requests mit PostgreSQL, Keycloak und Mailpit prüfen."""

from http import HTTPStatus

import pytest
from common_api_test import timeout
from requests import get

pytestmark = pytest.mark.rest


def test_post(neues_mitglied) -> None:
    response, daten, headers = neues_mitglied
    assert response.status_code == HTTPStatus.CREATED
    response = get(response.headers["Location"], headers=headers, timeout=timeout)
    assert response.status_code == HTTPStatus.OK
    mitglied = response.json()
    assert mitglied["email"] == daten["email"]

    mail = get("http://localhost:8025/api/v1/messages", timeout=timeout)
    assert mail.status_code == HTTPStatus.OK
    assert any(
        msg["Subject"] == f"Neues Mitglied: ID={mitglied['id']}"
        for msg in mail.json()["messages"]
    )
