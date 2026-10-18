"""Lesende Geschäftslogik ohne Verbindung zu PostgreSQL prüfen."""

from datetime import date
from unittest.mock import create_autospec, patch

import pytest

from mitglied.entity import Geschlecht, Mitglied
from mitglied.repository import (
    MitgliedRepository,
    MitgliedSuchparameter,
    Pageable,
    Slice,
)
from mitglied.service import (
    EmailExistsError,
    MitgliedDTO,
    MitgliedService,
    MitgliedWriteService,
    NotFoundError,
    VersionOutdatedError,
)


@pytest.fixture
def mitglied() -> Mitglied:
    """Ein Mitglied als Ausgangsdaten für Service-Tests bereitstellen."""
    return Mitglied(
        id=1000,
        version=1,
        vorname="Alex",
        nachname="Muster",
        email="alex@example.org",
        geburtsdatum=date(2000, 1, 1),
        geschlecht=Geschlecht.DIVERS,
        vertrag=None,
        zahlungen=[],
        erzeugt=None,
        aktualisiert=None,
    )


def test_find_wandelt_daten_um_und_behaelt_gesamtzahl(mitglied) -> None:
    repo = create_autospec(MitgliedRepository, instance=True)
    gesamtzahl = 12
    repo.find.return_value = Slice(content=(mitglied,), total_elements=gesamtzahl)
    suchparameter = MitgliedSuchparameter(nachname="Muster")
    pageable = Pageable(size=1, number=0)

    with patch("mitglied.service.mitglied_service.Session") as sessions:
        session = sessions.return_value.__enter__.return_value
        ergebnis = MitgliedService(repo).find(suchparameter, pageable)
        repo.find.assert_called_once_with(
            suchparameter=suchparameter, pageable=pageable, session=session
        )
        session.commit.assert_called_once_with()
        sessions.return_value.__exit__.assert_called_once_with(None, None, None)

    assert ergebnis.total_elements == gesamtzahl
    assert len(ergebnis.content) == 1
    dto = ergebnis.content[0]
    assert isinstance(dto, MitgliedDTO)
    assert dto.id == mitglied.id
    assert dto.nachname == "Muster"
    assert dto.vertrag is None
    assert dto.interessen is None


@pytest.mark.parametrize(
    "suchparameter", [None, MitgliedSuchparameter(nachname="Fehlt")]
)
def test_find_ohne_treffer_meldet_fehler(suchparameter) -> None:
    repo = create_autospec(MitgliedRepository, instance=True)
    repo.find.return_value = Slice(content=(), total_elements=0)

    with patch("mitglied.service.mitglied_service.Session") as sessions:
        session = sessions.return_value.__enter__.return_value
        with pytest.raises(NotFoundError) as fehler:
            MitgliedService(repo).find(suchparameter, Pageable(size=5, number=0))
        assert fehler.value.suchparameter is suchparameter
        session.commit.assert_not_called()
        sessions.return_value.__exit__.assert_called_once()


def test_update_uebernimmt_daten_und_erhoeht_dto_version(mitglied) -> None:
    repo = create_autospec(MitgliedRepository, instance=True)
    repo.find_by_id.return_value = mitglied
    repo.update.return_value = mitglied
    repo.exists_email_other_id.return_value = False
    neue_daten = Mitglied(
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
    vorherige_version = mitglied.version

    with patch("mitglied.service.mitglied_write_service.Session") as sessions:
        session = sessions.return_value.__enter__.return_value
        dto = MitgliedWriteService(repo).update(neue_daten, 1000, vorherige_version)
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
        ("email_vergeben", EmailExistsError),
        ("update_ohne_treffer", NotFoundError),
    ],
)
def test_update_fehler_ohne_commit(mitglied, fall, fehlerklasse) -> None:
    repo = create_autospec(MitgliedRepository, instance=True)
    repo.find_by_id.return_value = None if fall == "nicht_gefunden" else mitglied
    repo.update.return_value = None
    repo.exists_email_other_id.return_value = True
    neue_daten = Mitglied(
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
    if fall == "update_ohne_treffer":
        neue_daten.email = mitglied.email
    version = 0 if fall == "veraltet" else mitglied.version

    with patch("mitglied.service.mitglied_write_service.Session") as sessions:
        session = sessions.return_value.__enter__.return_value
        with pytest.raises(fehlerklasse):
            MitgliedWriteService(repo).update(neue_daten, 1000, version)
        session.commit.assert_not_called()
        if fall != "update_ohne_treffer":
            repo.update.assert_not_called()
        sessions.return_value.__exit__.assert_called_once()


def test_delete_by_id_ruft_repository_auf_und_committet() -> None:
    repo = create_autospec(MitgliedRepository, instance=True)
    with patch("mitglied.service.mitglied_write_service.Session") as sessions:
        session = sessions.return_value.__enter__.return_value
        MitgliedWriteService(repo).delete_by_id(1000)
        repo.delete_by_id.assert_called_once_with(mitglied_id=1000, session=session)
        session.commit.assert_called_once_with()
        sessions.return_value.__exit__.assert_called_once_with(None, None, None)
