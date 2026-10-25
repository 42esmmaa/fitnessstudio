"""Erster Test: GET-Request auf / mit dem TestClient von FastAPI."""

from http import HTTPStatus

from fastapi.testclient import TestClient

from mitglied import app

client = TestClient(app)


def test_hello() -> None:
    response = client.get("/")

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"message": "Hello Fitnessstudio"}
