"""Geschäftslogik zum Anlegen von Mitgliedern prüfen."""

from unittest.mock import create_autospec, patch

import pytest
from sqlalchemy.exc import IntegrityError

from mitglied.repository import (
    MitgliedRepository,
)
from mitglied.security import UserService
from mitglied.service import (
    EmailExistsError,
    MitgliedWriteService,
)


def test_create_benutzer_und_mitglied(mitglied) -> None:
    repo = create_autospec(MitgliedRepository, instance=True)
    repo.exists_email.return_value = False
    repo.create.return_value = mitglied
    user_service = create_autospec(UserService, instance=True)
    user_service.username_exists.return_value = False
    user_service.email_exists.return_value = False
    with patch("mitglied.service.mitglied_write_service.Session") as sessions:
        session = sessions.return_value.__enter__.return_value
        dto = MitgliedWriteService(repo, user_service).create(mitglied)
        repo.exists_email.assert_called_once_with(email=mitglied.email, session=session)
        repo.create.assert_called_once_with(mitglied=mitglied, session=session)
        session.commit.assert_called_once_with()
    user_service.create_user.assert_called_once()
    user = user_service.create_user.call_args.args[0]
    assert user.username == mitglied.email
    assert user.email == mitglied.email
    assert user.vorname == mitglied.vorname
    assert user.nachname == mitglied.nachname
    assert dto.id == mitglied.id


@pytest.mark.parametrize("duplikat", ["username", "email", "datenbank"])
def test_create_email_bereits_vergeben(mitglied, duplikat) -> None:
    repo = create_autospec(MitgliedRepository, instance=True)
    repo.exists_email.return_value = duplikat == "datenbank"
    user_service = create_autospec(UserService, instance=True)
    user_service.username_exists.return_value = duplikat == "username"
    user_service.email_exists.return_value = duplikat == "email"
    with patch("mitglied.service.mitglied_write_service.Session") as sessions:
        with pytest.raises(EmailExistsError) as fehler:
            MitgliedWriteService(repo, user_service).create(mitglied)
        assert fehler.value.email == mitglied.email
        repo.create.assert_not_called()
        sessions.return_value.__enter__.return_value.commit.assert_not_called()
    # bei jedem Duplikat wird gar kein Keycloak-User angelegt
    user_service.create_user.assert_not_called()


def test_create_keycloak_fehler_ohne_datenbankzugriff(mitglied) -> None:
    repo = create_autospec(MitgliedRepository, instance=True)
    user_service = create_autospec(UserService, instance=True)
    user_service.username_exists.return_value = False
    user_service.email_exists.return_value = False
    user_service.create_user.side_effect = ConnectionError("Testfehler")
    repo.exists_email.return_value = False
    with (
        patch("mitglied.service.mitglied_write_service.Session"),
        pytest.raises(ConnectionError),
    ):
        MitgliedWriteService(repo, user_service).create(mitglied)
    repo.create.assert_not_called()
    user_service.delete_user.assert_not_called()


@pytest.mark.parametrize(
    ("db_fehler", "erwartet"),
    [
        (IntegrityError("INSERT", {}, Exception("unique")), EmailExistsError),
        (ConnectionError("DB weg"), ConnectionError),
    ],
)
def test_create_db_fehler_loescht_keycloak_user(mitglied, db_fehler, erwartet) -> None:
    repo = create_autospec(MitgliedRepository, instance=True)
    repo.exists_email.return_value = False
    repo.create.side_effect = db_fehler
    user_service = create_autospec(UserService, instance=True)
    user_service.username_exists.return_value = False
    user_service.email_exists.return_value = False
    user_service.create_user.return_value = "keycloak-id"
    with (
        patch("mitglied.service.mitglied_write_service.Session"),
        pytest.raises(erwartet),
    ):
        MitgliedWriteService(repo, user_service).create(mitglied)
    user_service.delete_user.assert_called_once_with("keycloak-id")
