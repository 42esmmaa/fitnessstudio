"""PUT-Requests mit Versionsprüfung gegen den laufenden Appserver prüfen."""

from http import HTTPStatus

import pytest
from common_api_test import timeout
from requests import get, put

pytestmark = pytest.mark.rest


def test_put(neues_mitglied) -> None:
    angelegt, daten, headers = neues_mitglied
    location = angelegt.headers["Location"]
    response = get(location, headers=headers, timeout=timeout)
    assert response.status_code == HTTPStatus.OK
    etag = response.headers["ETag"]
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
        headers={**headers, "If-Match": etag},
        timeout=timeout,
    )
    assert response.status_code == HTTPStatus.NO_CONTENT
    assert response.headers["ETag"] != etag
    response = put(
        location,
        json=update,
        headers={**headers, "If-Match": etag},
        timeout=timeout,
    )
    assert response.status_code == HTTPStatus.PRECONDITION_FAILED
