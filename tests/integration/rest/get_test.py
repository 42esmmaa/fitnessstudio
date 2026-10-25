"""GET-Requests zur Mitgliedersuche prüfen."""

from http import HTTPStatus

import pytest
from common_api_test import login, rest_url, timeout
from requests import get

pytestmark = pytest.mark.rest


def test_admin_suche() -> None:
    response = get(
        rest_url, headers={"Authorization": f"Bearer {login()}"}, timeout=timeout
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json()["content"]
