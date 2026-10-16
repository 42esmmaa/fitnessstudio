"""Entity-Zuordnungen ohne externen Datenbankserver prüfen."""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from mitglied.entity import Base, Geschlecht, Mitglied, Tarif, Vertrag, Zahlung


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
        vertrag=Vertrag(
            beginn=date(2026, 10, 1),
            monatlicher_beitrag=Decimal("29.90"),
            tarif=Tarif.STUDENT,
            getraenkeflat=True,
        ),
        zahlungen=[
            Zahlung(betrag=Decimal("29.90"), zahlungsdatum=date(2026, 10, 1)),
            Zahlung(betrag=Decimal("29.90"), zahlungsdatum=date(2026, 11, 1)),
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
