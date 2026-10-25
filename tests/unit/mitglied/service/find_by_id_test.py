"""Geschäftslogik zur Suche nach Mitglied-ID prüfen."""

from unittest.mock import create_autospec, patch

import pytest

from mitglied.repository import (
    MitgliedRepository,
)
from mitglied.security import Role, User
from mitglied.service import (
    ForbiddenError,
    MitgliedService,
    NotFoundError,
)


@pytest.mark.parametrize(
    ("rolle", "email"),
    [
        (Role.ADMIN, "admin@example.org"),
        (Role.MITGLIED, "alex@example.org"),
        (Role.MITGLIED, "Alex@Example.org"),
    ],
)
def test_find_by_id_berechtigter_user(mitglied, rolle, email) -> None:
    repo = create_autospec(MitgliedRepository, instance=True)
    repo.find_by_id.return_value = mitglied
    user = User(
        username="test", email=email, vorname="Alex", nachname="Muster", roles=[rolle]
    )
    with patch("mitglied.service.mitglied_service.Session") as sessions:
        session = sessions.return_value.__enter__.return_value
        dto = MitgliedService(repo).find_by_id(1000, user)
        repo.find_by_id.assert_called_once_with(session=session, mitglied_id=1000)
        session.commit.assert_called_once_with()
    assert dto.id == mitglied.id
    assert dto.email == mitglied.email


@pytest.mark.parametrize(
    ("rolle", "vorhanden", "fehlerklasse"),
    [
        (Role.ADMIN, False, NotFoundError),
        (Role.MITGLIED, False, ForbiddenError),
        (Role.MITGLIED, True, ForbiddenError),
    ],
)
def test_find_by_id_verweigert_zugriff(
    mitglied, rolle, vorhanden, fehlerklasse
) -> None:
    repo = create_autospec(MitgliedRepository, instance=True)
    repo.find_by_id.return_value = mitglied if vorhanden else None
    user = User(
        username="fremd",
        email="fremd@example.org",
        vorname="Kim",
        nachname="Muster",
        roles=[rolle],
    )
    with patch("mitglied.service.mitglied_service.Session") as sessions:
        session = sessions.return_value.__enter__.return_value
        with pytest.raises(fehlerklasse):
            MitgliedService(repo).find_by_id(1000, user)
        session.commit.assert_not_called()
