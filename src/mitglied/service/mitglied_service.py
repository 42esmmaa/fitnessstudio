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
from mitglied.service.exceptions import NotFoundError
from mitglied.service.mitglied_dto import MitgliedDTO

__all__ = ["MitgliedService"]


class MitgliedService:
    """Service-Klasse mit Geschäftslogik für Mitglied."""

    def __init__(self, repo: MitgliedRepository) -> None:
        """Konstruktor mit abhängigem MitgliedRepository."""
        self.repo: MitgliedRepository = repo

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
