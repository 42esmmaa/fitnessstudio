"""DELETE-Requests gegen den laufenden Appserver prüfen."""

from http import HTTPStatus

import pytest
from common_api_test import timeout
from requests import delete, get

pytestmark = pytest.mark.rest


def test_delete(neues_mitglied) -> None:
    angelegt, _daten, headers = neues_mitglied
    location = angelegt.headers["Location"]
    response = delete(location, headers=headers, timeout=timeout)
    assert response.status_code == HTTPStatus.NO_CONTENT
    response = get(location, headers=headers, timeout=timeout)
    assert response.status_code == HTTPStatus.NOT_FOUND
