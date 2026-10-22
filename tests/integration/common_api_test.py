"""Allgemeine Daten für Integrationstests gegen den laufenden Appserver."""

from http import HTTPStatus
from os import getenv
from pathlib import Path
from typing import Final

from dotenv import dotenv_values
from requests import request

base_url: Final = getenv("FITNESSSTUDIO_BASE_URL", "http://127.0.0.1:8000")
rest_url: Final = f"{base_url}/rest"
token_path: Final = "/auth/token"  # ruff: ignore[hardcoded-password-string]
timeout: Final = 10
keycloak_certificate_path: Final = str(
    Path("extras") / "compose" / "keycloak" / "tls" / "certificate.crt"
)


def login(username: str = "admin") -> str:
    """Am Appserver anmelden, ohne Zugangsdaten oder Token auszugeben."""
    response = request(
        method="QUERY",
        url=f"{base_url}{token_path}",
        json={
            "username": username,
            "password": dotenv_values(".env")["KEYCLOAK_ADMIN_PASSWORD"],
        },
        timeout=timeout,
    )
    assert response.status_code == HTTPStatus.OK
    return response.json()["token"]
