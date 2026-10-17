"""Repository fuer persistente Mitgliedsdaten."""

from typing import Final

from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from mitglied.entity import Mitglied

__all__ = ["MitgliedRepository"]


class MitgliedRepository:
    """Repository-Klasse mit CRUD-Methoden für die Entity-Klasse Mitglied."""

    def find_by_id(self, mitglied_id: int | None, session: Session) -> Mitglied | None:
        """Suche mit der Mitglied-ID.

        :param mitglied_id: ID des gesuchten Mitglieds
        :param session: Session für SQLAlchemy
        :return: Das gefundene Mitglied oder None
        :rtype: Mitglied | None
        """
        logger.debug("mitglied_id={}", mitglied_id)  # NOSONAR

        if mitglied_id is None:
            return None

        statement: Final = (
            select(Mitglied)
            .options(joinedload(Mitglied.vertrag))
            .where(Mitglied.id == mitglied_id)
        )
        mitglied: Final = session.scalar(statement)

        # mitglied: Final[Mitglied | None] = session.get(Mitglied, mitglied_id)

        logger.debug("{}", mitglied)
        return mitglied
