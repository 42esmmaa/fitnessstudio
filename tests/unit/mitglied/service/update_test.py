"""Geschäftslogik zum Ändern von Mitgliedern prüfen."""

from datetime import date
from unittest.mock import create_autospec, patch

import pytest

from mitglied.entity import Geschlecht, Mitglied
from mitglied.repository import (
    MitgliedRepository,
)
from mitglied.security import UserService
from mitglied.service import (
    EmailExistsError,
    ForbiddenError,
    MitgliedWriteService,
    NotFoundError,
    VersionOutdatedError,
)


@pytest.fixture
def neue_daten() -> Mitglied:
    """Neue Daten für ein Update."""
    return Mitglied(
        id=None,
        vorname="Kim",
        nachname="Muster",
        email="kim@example.org",
        geburtsdatum=date(2000, 1, 1),
        geschlecht=Geschlecht.DIVERS,
        vertrag=None,
        zahlungen=[],
        erzeugt=None,
        aktualisiert=None,
    )


def _write_service(repo) -> MitgliedWriteService:
    return MitgliedWriteService(
        repo, user_service=create_autospec(UserService, instance=True)
    )


@pytest.mark.parametrize("user_fixture", ["admin", "eigentuemer"])
def test_update_uebernimmt_daten_und_erhoeht_dto_version(
    request, mitglied, neue_daten, user_fixture
) -> None:
    user = request.getfixturevalue(user_fixture)
    repo = create_autospec(MitgliedRepository, instance=True)
    repo.find_by_id.return_value = mitglied
    repo.update.return_value = mitglied
    repo.exists_email_other_id.return_value = False
    vorherige_version = mitglied.version

    with patch("mitglied.service.mitglied_write_service.Session") as sessions:
        session = sessions.return_value.__enter__.return_value
        dto = _write_service(repo).update(
            neue_daten, 1000, vorherige_version, user=user
        )
        repo.exists_email_other_id.assert_called_once_with(
            mitglied_id=1000, email="kim@example.org", session=session
        )
        repo.update.assert_called_once_with(mitglied=mitglied, session=session)
        session.commit.assert_called_once_with()

    assert dto.vorname == "Kim"
    assert dto.email == "kim@example.org"
    assert dto.version == vorherige_version + 1


@pytest.mark.parametrize(
    ("fall", "fehlerklasse"),
    [
        ("nicht_gefunden", NotFoundError),
        ("veraltet", VersionOutdatedError),
        ("zu_neu", VersionOutdatedError),
        ("email_vergeben", EmailExistsError),
        ("update_ohne_treffer", NotFoundError),
    ],
)
def test_update_fehler_ohne_commit(
    mitglied, neue_daten, admin, fall, fehlerklasse
) -> None:
    repo = create_autospec(MitgliedRepository, instance=True)
    repo.find_by_id.return_value = None if fall == "nicht_gefunden" else mitglied
    repo.update.return_value = None
    repo.exists_email_other_id.return_value = True
    if fall == "update_ohne_treffer":
        neue_daten.email = mitglied.email
    version = {"veraltet": 0, "zu_neu": mitglied.version + 1}.get(
        fall, mitglied.version
    )

    with patch("mitglied.service.mitglied_write_service.Session") as sessions:
        session = sessions.return_value.__enter__.return_value
        with pytest.raises(fehlerklasse):
            _write_service(repo).update(neue_daten, 1000, version, user=admin)
        session.commit.assert_not_called()
        if fall != "update_ohne_treffer":
            repo.update.assert_not_called()
        sessions.return_value.__exit__.assert_called_once()


@pytest.mark.parametrize("vorhanden", [True, False])
def test_update_fremdes_mitglied_verboten(
    mitglied, neue_daten, fremdes_mitglied, vorhanden
) -> None:
    # Auch eine nicht-vorhandene ID liefert fuer Mitglieder 403 statt 404,
    # damit man nicht herausfinden kann, welche IDs es gibt
    repo = create_autospec(MitgliedRepository, instance=True)
    repo.find_by_id.return_value = mitglied if vorhanden else None

    with patch("mitglied.service.mitglied_write_service.Session") as sessions:
        session = sessions.return_value.__enter__.return_value
        with pytest.raises(ForbiddenError):
            _write_service(repo).update(
                neue_daten, 1000, mitglied.version, user=fremdes_mitglied
            )
        repo.update.assert_not_called()
        session.commit.assert_not_called()
