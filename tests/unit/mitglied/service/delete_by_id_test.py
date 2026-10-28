"""Geschäftslogik zum Löschen von Mitgliedern prüfen."""

from unittest.mock import create_autospec, patch

import pytest

from mitglied.repository import (
    MitgliedRepository,
)
from mitglied.security import UserService
from mitglied.service import (
    ForbiddenError,
    MitgliedWriteService,
)


def _write_service(repo) -> MitgliedWriteService:
    return MitgliedWriteService(
        repo, user_service=create_autospec(UserService, instance=True)
    )


@pytest.mark.parametrize("user_fixture", ["admin", "eigentuemer"])
def test_delete_by_id_ruft_repository_auf_und_committet(
    request, mitglied, user_fixture
) -> None:
    user = request.getfixturevalue(user_fixture)
    repo = create_autospec(MitgliedRepository, instance=True)
    repo.find_by_id.return_value = mitglied
    with patch("mitglied.service.mitglied_write_service.Session") as sessions:
        session = sessions.return_value.__enter__.return_value
        _write_service(repo).delete_by_id(1000, user=user)
        repo.delete_by_id.assert_called_once_with(mitglied_id=1000, session=session)
        session.commit.assert_called_once_with()
        sessions.return_value.__exit__.assert_called_once_with(None, None, None)


def test_delete_nicht_vorhanden_als_admin_ohne_fehler(admin) -> None:
    repo = create_autospec(MitgliedRepository, instance=True)
    repo.find_by_id.return_value = None
    with patch("mitglied.service.mitglied_write_service.Session") as sessions:
        _write_service(repo).delete_by_id(1000, user=admin)
        repo.delete_by_id.assert_not_called()
        sessions.return_value.__enter__.return_value.commit.assert_not_called()


@pytest.mark.parametrize("vorhanden", [True, False])
def test_delete_fremdes_mitglied_verboten(
    mitglied, fremdes_mitglied, vorhanden
) -> None:
    repo = create_autospec(MitgliedRepository, instance=True)
    repo.find_by_id.return_value = mitglied if vorhanden else None
    with patch("mitglied.service.mitglied_write_service.Session") as sessions:
        with pytest.raises(ForbiddenError):
            _write_service(repo).delete_by_id(1000, user=fremdes_mitglied)
        repo.delete_by_id.assert_not_called()
        sessions.return_value.__enter__.return_value.commit.assert_not_called()
