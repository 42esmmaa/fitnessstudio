"""QUERY-Requests zur Mitgliedersuche prüfen."""

from http import HTTPStatus

import pytest
from common_api_test import login, rest_url, timeout
from requests import request

pytestmark = pytest.mark.rest


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
