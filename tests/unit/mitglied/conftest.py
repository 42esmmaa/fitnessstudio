"""Fixtures für die Unit-Tests der Mitgliederverwaltung."""

from datetime import date

import pytest

from mitglied.entity import Geschlecht, Mitglied
from mitglied.security import Role, User


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


def _user(email: str, rolle: Role) -> User:
    return User(
        username=email,
        email=email,
        vorname="Alex",
        nachname="Muster",
        roles=[rolle],
    )


@pytest.fixture
def admin() -> User:
    """Ein Administrator aus dem Token."""
    return _user("admin@example.org", Role.ADMIN)


@pytest.fixture
def eigentuemer() -> User:
    """Das Mitglied aus der Fixture `mitglied` als eingeloggter User.

    Die Emailadresse im Token ist absichtlich in Großbuchstaben, weil der Vergleich
    ohne Groß-/Kleinschreibung erfolgen muss.
    """
    return _user("ALEX@example.org", Role.MITGLIED)


@pytest.fixture
def fremdes_mitglied() -> User:
    """Ein anderes Mitglied, dem die Daten der Fixture `mitglied` nicht gehören."""
    return _user("kim@example.org", Role.MITGLIED)
