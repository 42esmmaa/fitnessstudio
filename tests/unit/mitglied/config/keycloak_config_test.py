"""Quellen und Geheimhaltung der Keycloak-Konfiguration prüfen."""

from runpy import run_path

import pytest

from mitglied.config import config, keycloak


@pytest.fixture
def load_config(monkeypatch):
    """Konfiguration isoliert mit vorgegebenen Quellen einlesen."""

    def load(toml, umgebung):
        monkeypatch.setattr(config, "app_config", {"keycloak": toml})
        for name in (
            "KEYCLOAK_CLIENT_SECRET",
            "KEYCLOAK_ADMIN_USERNAME",
            "KEYCLOAK_ADMIN_PASSWORD",
        ):
            monkeypatch.delenv(name, raising=False)
        for name, wert in umgebung.items():
            monkeypatch.setenv(name, wert)
        return run_path(keycloak.__file__)

    return load


def test_umgebung_hat_vorrang(load_config) -> None:
    umgebung = {
        "KEYCLOAK_CLIENT_SECRET": "test-env-client",
        "KEYCLOAK_ADMIN_USERNAME": "test-admin",
        "KEYCLOAK_ADMIN_PASSWORD": "test-env-admin",
    }
    geladen = load_config(
        {"client-secret": "test-toml-client", "admin-password": "test-toml-admin"},
        umgebung,
    )
    assert (
        geladen["keycloak_config"].client_secret_key
        == umgebung["KEYCLOAK_CLIENT_SECRET"]
    )
    admin = geladen["keycloak_admin_config"]
    assert admin.username == umgebung["KEYCLOAK_ADMIN_USERNAME"]
    assert admin.password == umgebung["KEYCLOAK_ADMIN_PASSWORD"]
    assert admin.client_secret_key == umgebung["KEYCLOAK_CLIENT_SECRET"]
    assert umgebung["KEYCLOAK_CLIENT_SECRET"] not in repr(admin)
    assert umgebung["KEYCLOAK_ADMIN_PASSWORD"] not in repr(admin)


def test_toml_rueckfall_wie_vorlage(load_config) -> None:
    werte = {
        "client-secret": "test-toml-client",
        "admin": "test-admin",
        "admin-password": "test-toml-admin",
        "host": "localhost",
        "port": 8843,
    }
    geladen = load_config(werte, {})
    allgemein = geladen["keycloak_config"]
    admin = geladen["keycloak_admin_config"]
    assert allgemein.server_url == "https://localhost:8843/"
    assert allgemein.client_secret_key == werte["client-secret"]
    assert admin.username == werte["admin"]
    assert admin.password == werte["admin-password"]


def test_defaults_ohne_zugangsdaten(load_config) -> None:
    geladen = load_config({}, {})
    allgemein = geladen["keycloak_config"]
    assert allgemein.realm_name == "fitnessstudio"
    assert allgemein.client_id == "fitnessstudio-client"
    assert not allgemein.client_secret_key
    assert not geladen["keycloak_admin_config"].password
