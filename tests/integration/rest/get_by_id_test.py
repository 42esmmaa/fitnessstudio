"""GET-Requests mit Mitglied-ID und ETag prüfen."""

from http import HTTPStatus

import pytest
from common_api_test import login, rest_url, timeout
from requests import get

pytestmark = pytest.mark.rest


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


def test_get_by_id_etag(neues_mitglied) -> None:
    angelegt, _daten, headers = neues_mitglied
    location = angelegt.headers["Location"]
    response = get(location, headers=headers, timeout=timeout)
    assert response.status_code == HTTPStatus.OK
    etag = response.headers["ETag"]
    response = get(
        location,
        headers={**headers, "If-None-Match": etag},
        timeout=timeout,
    )
    assert response.status_code == HTTPStatus.NOT_MODIFIED
