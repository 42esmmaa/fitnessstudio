"""Geschäftslogik zum Schreiben von Mitgliedsdaten."""

from typing import Final

from loguru import logger

from mitglied.repository import MitgliedRepository, Session
from mitglied.security import User, UserService
from mitglied.service.exceptions import (
    EmailExistsError,
    NotFoundError,
    VersionOutdatedError,
)
from mitglied.service.mitglied_dto import MitgliedDTO
lazy from mitglied.entity import Mitglied

__all__ = ["MitgliedWriteService"]


class MitgliedWriteService:
    """Service-Klasse mit Geschäftslogik für Mitglied."""

    def __init__(self, repo: MitgliedRepository, user_service: UserService) -> None:
        """Konstruktor mit abhängigem MitgliedRepository und UserService."""
        self.repo: MitgliedRepository = repo
        self.user_service: UserService = user_service

    def create(self, mitglied: Mitglied) -> MitgliedDTO:
        """Ein neues Mitglied anlegen.

        :param mitglied: Das neue Mitglied ohne ID
        :return: Das neu angelegte Mitglied mit generierter ID
        :rtype: MitgliedDTO
        :raises EmailExistsError: Falls die Emailadresse bereits existiert
        """
        logger.debug(
            "mitglied={}, vertrag={}, zahlungen={}",
            mitglied,
            mitglied.vertrag,
            mitglied.zahlungen,
        )

        email: Final = mitglied.email
        if self.user_service.username_exists(email):
            raise EmailExistsError(email=email)
        if self.user_service.email_exists(email):
            raise EmailExistsError(email=email)

        user: Final = User(
            username=email,
            email=email,
            nachname=mitglied.nachname,
            vorname=mitglied.vorname,
            password="p",  # ruff: ignore[hardcoded-password-func-arg] # NOSONAR
            roles=[],
        )
        user_id = self.user_service.create_user(user)
        logger.debug("user_id={}", user_id)

        with Session() as session:
            if self.repo.exists_email(email=email, session=session):
                raise EmailExistsError(email=email)

            mitglied_db: Final = self.repo.create(mitglied=mitglied, session=session)
            mitglied_dto: Final = MitgliedDTO.from_mitglied(mitglied_db)
            session.commit()

        # TODO User aus Keycloak loeschen, falls die DB-Transaktion fehlschlaegt

        logger.debug("mitglied_dto={}", mitglied_dto)
        return mitglied_dto

    def update(self, mitglied: Mitglied, mitglied_id: int, version: int) -> MitgliedDTO:
        """Daten eines Mitglieds ändern.

        :param mitglied: Die neuen Daten
        :param mitglied_id: ID des zu aktualisierenden Mitglieds
        :param version: Version für optimistische Synchronisation
        :return: Das aktualisierte Mitglied
        :rtype: MitgliedDTO
        :raises NotFoundError: Falls das zu aktualisierende Mitglied nicht existiert
        :raises VersionOutdatedError: Falls die Versionsnummer nicht aktuell ist
        :raises EmailExistsError: Falls die Emailadresse bereits existiert
        """
        logger.debug("mitglied_id={}, version={}, {}", mitglied_id, version, mitglied)

        with Session() as session:
            if (
                mitglied_db := self.repo.find_by_id(
                    mitglied_id=mitglied_id,
                    session=session,
                )
            ) is None:
                raise NotFoundError(mitglied_id)
            if mitglied_db.version > version:
                raise VersionOutdatedError(version)

            email: Final = mitglied.email
            if email != mitglied_db.email and self.repo.exists_email_other_id(
                mitglied_id=mitglied_id,
                email=email,
                session=session,
            ):
                raise EmailExistsError(email)

            mitglied_db.set(mitglied)
            if (
                mitglied_updated := self.repo.update(
                    mitglied=mitglied_db, session=session
                )
            ) is None:
                raise NotFoundError(mitglied_id)
            mitglied_dto: Final = MitgliedDTO.from_mitglied(mitglied_updated)
            logger.debug("{}", mitglied_dto)

            session.commit()
            # CAVEAT: Die erhoehte Versionsnummer ist erst COMMIT sichtbar
            mitglied_dto.version += 1
            return mitglied_dto

    def delete_by_id(self, mitglied_id: int) -> None:
        """Ein Mitglied anhand seiner ID löschen.

        :param mitglied_id: ID des zu löschenden Mitglieds
        """
        logger.debug("mitglied_id={}", mitglied_id)
        with Session() as session:
            self.repo.delete_by_id(mitglied_id=mitglied_id, session=session)
            session.commit()
