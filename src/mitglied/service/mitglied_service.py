"""Geschäftslogik zum Lesen von Mitgliedsdaten."""

from typing import Final

from loguru import logger

from mitglied.repository import (
    MitgliedRepository,
    MitgliedSuchparameter,
    Pageable,
    Session,
    Slice,
)
from mitglied.security import Role, User
from mitglied.service.exceptions import ForbiddenError, NotFoundError
from mitglied.service.mitglied_dto import MitgliedDTO

__all__ = ["MitgliedService"]


class MitgliedService:
    """Service-Klasse mit Geschäftslogik für Mitglied."""

    def __init__(self, repo: MitgliedRepository) -> None:
        """Konstruktor mit abhängigem MitgliedRepository."""
        self.repo: MitgliedRepository = repo

    def find_by_id(self, mitglied_id: int, user: User) -> MitgliedDTO:
        """Suche mit der Mitglied-ID.

        :param mitglied_id: ID für die Suche
        :param user: User aus dem Token
        :return: Das gefundene Mitglied
        :rtype: MitgliedDTO
        :raises NotFoundError: Falls kein Mitglied gefunden
        :raises ForbiddenError: Falls die Mitgliedsdaten nicht gelesen werden dürfen
        """
        logger.debug("mitglied_id={}, user={}", mitglied_id, user)
        with Session() as session:
            user_is_admin: Final = Role.ADMIN in user.roles

            if (
                mitglied := self.repo.find_by_id(
                    session=session, mitglied_id=mitglied_id
                )
            ) is None:
                if user_is_admin:
                    message: Final = f"Kein Mitglied mit der ID {mitglied_id}"
                    logger.debug("NotFoundError: {}", message)
                    raise NotFoundError(mitglied_id=mitglied_id)
                logger.debug("nicht admin")
                raise ForbiddenError

            if mitglied.email != user.email.strip().lower() and not user_is_admin:
                logger.debug(
                    "mitglied.email={}, user.email={}, user.roles={}",
                    mitglied.email,
                    user.email,
                    user.roles,
                )
                raise ForbiddenError

            mitglied_dto: Final = MitgliedDTO.from_mitglied(mitglied)
            session.commit()

        logger.debug("{}", mitglied_dto)
        return mitglied_dto

    def find(
        self,
        suchparameter: MitgliedSuchparameter | None,
        pageable: Pageable,
    ) -> Slice[MitgliedDTO]:
        """Suche mit Suchparameter.

        :param suchparameter: Suchparameter oder None
        :return: Liste der gefundenen Mitglieder
        :rtype: Slice[MitgliedDTO]
        :raises NotFoundError: Falls keine Mitglieder gefunden wurden
        """
        logger.debug("{}", suchparameter)
        with Session() as session:
            mitglied_slice: Final = self.repo.find(
                suchparameter=suchparameter,
                pageable=pageable,
                session=session,
            )
            if len(mitglied_slice.content) == 0:
                raise NotFoundError(suchparameter=suchparameter)

            mitglieder_dto: Final = tuple(
                MitgliedDTO.from_mitglied(mitglied)
                for mitglied in mitglied_slice.content
            )
            session.commit()

        mitglieder_dto_slice = Slice(
            content=mitglieder_dto,
            total_elements=mitglied_slice.total_elements,
        )
        logger.debug("{}", mitglieder_dto_slice)
        return mitglieder_dto_slice
