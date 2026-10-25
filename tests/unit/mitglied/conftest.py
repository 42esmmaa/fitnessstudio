"""Fixtures für die Unit-Tests der Mitgliederverwaltung."""

from datetime import date

import pytest

from mitglied.entity import Geschlecht, Mitglied


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
