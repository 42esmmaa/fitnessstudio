"""Geschäftslogik zum Löschen von Mitgliedern prüfen."""

from unittest.mock import create_autospec, patch

from mitglied.repository import (
    MitgliedRepository,
)
from mitglied.security import UserService
from mitglied.service import (
    MitgliedWriteService,
)


def test_delete_by_id_ruft_repository_auf_und_committet() -> None:
    repo = create_autospec(MitgliedRepository, instance=True)
    with patch("mitglied.service.mitglied_write_service.Session") as sessions:
        session = sessions.return_value.__enter__.return_value
        MitgliedWriteService(
            repo, user_service=create_autospec(UserService, instance=True)
        ).delete_by_id(1000)
        repo.delete_by_id.assert_called_once_with(mitglied_id=1000, session=session)
        session.commit.assert_called_once_with()
        sessions.return_value.__exit__.assert_called_once_with(None, None, None)
