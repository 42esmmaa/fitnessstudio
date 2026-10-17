"""Entity-Zuordnungen ohne externen Datenbankserver prüfen."""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from mitglied.entity import Base, Geschlecht, Mitglied, Tarif, Vertrag, Zahlung
from mitglied.repository import MitgliedRepository, MitgliedSuchparameter, Pageable


@pytest.fixture
def engine():
    """Eine leere Datenbank im Arbeitsspeicher bereitstellen."""
    database = create_engine("sqlite://")
    Base.metadata.create_all(database)
    yield database
    database.dispose()


def neues_mitglied() -> Mitglied:
    """Ein Mitglied mit Vertrag und zwei Zahlungen erzeugen."""
    return Mitglied(
        vorname="Alex",
        nachname="Muster",
        email="alex@example.org",
        geburtsdatum=date(2000, 1, 1),
        geschlecht=Geschlecht.DIVERS,
        interessen=["Krafttraining", "Yoga"],
        id=None,
        erzeugt=None,
        aktualisiert=None,
        vertrag=Vertrag(
            beginn=date(2026, 10, 1),
            monatlicher_beitrag=Decimal("29.90"),
            tarif=Tarif.STUDENT,
            getraenkeflat=True,
            id=None,
            mitglied_id=None,
            mitglied=None,
        ),
        zahlungen=[
            Zahlung(
                betrag=Decimal("29.90"),
                zahlungsdatum=date(2026, 10, 1),
                id=None,
                mitglied_id=None,
                mitglied=None,
            ),
            Zahlung(
                betrag=Decimal("29.90"),
                zahlungsdatum=date(2026, 11, 1),
                id=None,
                mitglied_id=None,
                mitglied=None,
            ),
        ],
    )


def test_speichern_und_laden(engine) -> None:
    with Session(engine) as session:
        mitglied = neues_mitglied()
        session.add(mitglied)
        session.commit()
        session.expunge_all()

        geladen = session.scalars(select(Mitglied)).one()
        assert geladen.interessen == ["Krafttraining", "Yoga"]
        assert geladen.geschlecht is Geschlecht.DIVERS
        assert geladen.erzeugt is not None
        assert geladen.aktualisiert is not None
        assert geladen.version == 1
        assert geladen.vertrag is not None
        assert geladen.vertrag.monatlicher_beitrag == Decimal("29.90")
        assert geladen.vertrag.tarif is Tarif.STUDENT
        assert geladen.vertrag.getraenkeflat is True
        assert geladen.vertrag.mitglied is geladen
        assert [zahlung.betrag for zahlung in geladen.zahlungen] == [
            Decimal("29.90"),
            Decimal("29.90"),
        ]
        assert all(zahlung.mitglied is geladen for zahlung in geladen.zahlungen)


def test_email_eindeutig(engine) -> None:
    with Session(engine) as session:
        session.add_all([neues_mitglied(), neues_mitglied()])
        with pytest.raises(IntegrityError):
            session.commit()


def test_ohne_interessen(engine) -> None:
    mitglied = Mitglied(
        vorname="Alex",
        nachname="Muster",
        email="alex@example.org",
        geburtsdatum=date(2000, 1, 1),
        geschlecht=Geschlecht.DIVERS,
        id=None,
        vertrag=None,
        zahlungen=[],
        erzeugt=None,
        aktualisiert=None,
    )
    assert mitglied.interessen is None
    with Session(engine) as session:
        session.add(mitglied)
        session.commit()
        session.expunge_all()
        geladen = session.scalars(select(Mitglied)).one()
        assert geladen.interessen is None


def test_vertrag_eindeutig(engine) -> None:
    with Session(engine) as session:
        mitglied = neues_mitglied()
        session.add(mitglied)
        session.commit()
        with pytest.raises(IntegrityError):
            session.execute(
                insert(Vertrag).values(
                    mitglied_id=mitglied.id,
                    beginn=date(2026, 11, 1),
                    monatlicher_beitrag=Decimal("39.90"),
                    tarif=Tarif.BASIC,
                    getraenkeflat=False,
                )
            )


def test_versionsschutz(engine) -> None:
    with Session(engine) as session:
        session.add(neues_mitglied())
        session.commit()

    with Session(engine) as erste, Session(engine) as zweite:
        aktuell = erste.scalars(select(Mitglied)).one()
        veraltet = zweite.scalars(select(Mitglied)).one()
        vorherige_version = aktuell.version
        aktuell.vorname = "Kim"
        erste.commit()
        assert aktuell.version == vorherige_version + 1
        veraltet.vorname = "Robin"
        with pytest.raises(StaleDataError):
            zweite.commit()


def test_vergleich_anhand_der_id() -> None:
    erstes = neues_mitglied()
    zweites = neues_mitglied()
    dasselbe = erstes
    assert erstes == dasselbe
    assert erstes != zweites
    erstes.id = 1000
    zweites.id = 1000
    assert erstes == zweites
    assert hash(erstes) == hash(zweites)
    assert erstes != object()


def test_set_uebernimmt_nur_fachdaten() -> None:
    bisher = neues_mitglied()
    geaendert = neues_mitglied()
    geaendert.vorname = "Kim"
    geaendert.interessen = ["Schwimmen"]
    bisherige_id = 1000
    bisher.id = bisherige_id
    bisher.set(geaendert)
    assert bisher.vorname == "Kim"
    assert bisher.interessen == ["Schwimmen"]
    assert bisher.id == bisherige_id
    assert bisher.vertrag is not geaendert.vertrag


def test_vergleich_und_ausgabe_ohne_beziehungen(engine) -> None:
    with Session(engine) as session:
        session.add(neues_mitglied())
        session.commit()
        geladen = session.scalars(select(Mitglied)).one()
        session.expunge_all()

    anderes = neues_mitglied()
    anderes.id = geladen.id
    assert geladen == anderes
    assert hash(geladen) == hash(anderes)
    assert "Mitglied(" in repr(geladen)
    assert "Vertrag(" not in repr(geladen)


def test_repository_find_by_id_laedt_vertrag(engine) -> None:
    with Session(engine) as session:
        mitglied = neues_mitglied()
        session.add(mitglied)
        session.commit()
        mitglied_id = mitglied.id
        session.expunge_all()

        gefunden = MitgliedRepository().find_by_id(mitglied_id, session)
        assert gefunden is not None
        assert gefunden.id == mitglied_id
        session.expunge_all()

    assert gefunden.vertrag is not None
    assert gefunden.vertrag.tarif is Tarif.STUDENT


@pytest.mark.parametrize("mitglied_id", [None, 9999])
def test_repository_find_by_id_ohne_treffer(engine, mitglied_id) -> None:
    with Session(engine) as session:
        assert MitgliedRepository().find_by_id(mitglied_id, session) is None


@pytest.mark.parametrize(
    ("suchparameter", "size", "number", "erwartete_anzahl", "gesamt"),
    [
        (None, 1, 0, 1, 2),
        (MitgliedSuchparameter(), 1, 1, 1, 2),
        (None, 1, 2, 0, 2),
        (None, 0, 0, 2, 2),
        (MitgliedSuchparameter(email="alex@example.org"), 5, 0, 1, 1),
        (MitgliedSuchparameter(email="fehlt@example.org"), 5, 0, 0, 0),
        (MitgliedSuchparameter(nachname="mUs"), 1, 0, 1, 2),
        (MitgliedSuchparameter(nachname="mUs"), 1, 1, 1, 2),
        (MitgliedSuchparameter(nachname="mUs"), 0, 0, 2, 2),
        (MitgliedSuchparameter(nachname="Fehlt"), 5, 0, 0, 0),
        (
            MitgliedSuchparameter(email="alex@example.org", nachname="Fehlt"),
            5,
            0,
            1,
            1,
        ),
    ],
)
def test_repository_find(  # ruff: ignore[too-many-arguments]
    engine, *, suchparameter, size, number, erwartete_anzahl, gesamt
) -> None:
    with Session(engine) as session:
        erstes = neues_mitglied()
        zweites = neues_mitglied()
        zweites.email = "kim@example.org"
        session.add_all([erstes, zweites])
        session.commit()
        session.expunge_all()

        ergebnis = MitgliedRepository().find(
            suchparameter=suchparameter,
            pageable=Pageable(size=size, number=number),
            session=session,
        )
        assert len(ergebnis.content) == erwartete_anzahl
        assert ergebnis.total_elements == gesamt
        if suchparameter is not None and suchparameter.email == "alex@example.org":
            assert ergebnis.content[0].email == "alex@example.org"
        session.expunge_all()

    assert all(mitglied.vertrag is not None for mitglied in ergebnis.content)


@pytest.mark.parametrize(
    ("email", "erwartet"),
    [("alex@example.org", True), ("fehlt@example.org", False)],
)
def test_repository_exists_email(engine, email, erwartet) -> None:
    with Session(engine) as session:
        session.add(neues_mitglied())
        session.commit()
        assert MitgliedRepository().exists_email(email, session) is erwartet


def test_repository_exists_email_other_id(engine) -> None:
    with Session(engine) as session:
        erstes = neues_mitglied()
        zweites = neues_mitglied()
        zweites.email = "kim@example.org"
        session.add_all([erstes, zweites])
        session.commit()
        assert erstes.id is not None
        repository = MitgliedRepository()
        assert not repository.exists_email_other_id(
            "alex@example.org", erstes.id, session
        )
        assert repository.exists_email_other_id("kim@example.org", erstes.id, session)
        assert not repository.exists_email_other_id(
            "fehlt@example.org", erstes.id, session
        )
