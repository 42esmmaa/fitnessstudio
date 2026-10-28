"""Geschäftslogik zum Schreiben von Mitgliedsdaten."""

from typing import Final

from loguru import logger
from sqlalchemy.exc import IntegrityError

from mitglied.repository import MitgliedRepository, Session
from mitglied.security import Role, User, UserService
from mitglied.service.exceptions import (
    EmailExistsError,
    ForbiddenError,
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
        # Zuerst die eigene DB pruefen, damit bei einer vergebenen Emailadresse
        # gar nicht erst ein Benutzer in Keycloak angelegt wird
        with Session() as session:
            if self.repo.exists_email(email=email, session=session):
                raise EmailExistsError(email=email)
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
        user_id: Final = self.user_service.create_user(user)
        logger.debug("user_id={}", user_id)

        # Kompensation: Schlaegt die DB-Transaktion fehl, wird der soeben angelegte
        # Keycloak-User wieder geloescht, damit kein verwaister Login uebrig bleibt
        try:
            with Session() as session:
                mitglied_db: Final = self.repo.create(
                    mitglied=mitglied, session=session
                )
                mitglied_dto: Final = MitgliedDTO.from_mitglied(mitglied_db)
                session.commit()
        except IntegrityError as err:
            # paralleler Request mit derselben Emailadresse: der UNIQUE-Index greift
            self.user_service.delete_user(user_id)
            raise EmailExistsError(email=email) from err
        except Exception:
            self.user_service.delete_user(user_id)
            raise

        logger.debug("mitglied_dto={}", mitglied_dto)
        return mitglied_dto

    def update(
        self,
        mitglied: Mitglied,
        mitglied_id: int,
        version: int,
        user: User,
    ) -> MitgliedDTO:
        """Daten eines Mitglieds ändern.

        :param mitglied: Die neuen Daten
        :param mitglied_id: ID des zu aktualisierenden Mitglieds
        :param version: Version für optimistische Synchronisation
        :param user: User aus dem Token
        :return: Das aktualisierte Mitglied
        :rtype: MitgliedDTO
        :raises NotFoundError: Falls das zu aktualisierende Mitglied nicht existiert
        :raises ForbiddenError: Falls ein Mitglied fremde Daten ändern will
        :raises VersionOutdatedError: Falls die Versionsnummer nicht aktuell ist
        :raises EmailExistsError: Falls die Emailadresse bereits existiert
        """
        logger.debug("mitglied_id={}, version={}, {}", mitglied_id, version, mitglied)

        with Session() as session:
            mitglied_db: Final = self.repo.find_by_id(
                mitglied_id=mitglied_id,
                session=session,
            )
            self._pruefe_schreibzugriff(mitglied_db, mitglied_id, user)
            if mitglied_db is None:
                raise NotFoundError(mitglied_id)
            # != statt >: auch eine "zu neue" Version passt nicht zu den Daten,
            # die der Client tatsaechlich gelesen hat
            if mitglied_db.version != version:
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

    def delete_by_id(self, mitglied_id: int, user: User) -> None:
        """Ein Mitglied anhand seiner ID löschen.

        Für Administratoren ist das Löschen idempotent, d.h. ohne Fehler auch dann,
        wenn es kein Mitglied mit der ID (mehr) gibt.

        :param mitglied_id: ID des zu löschenden Mitglieds
        :param user: User aus dem Token
        :raises ForbiddenError: Falls ein Mitglied fremde Daten löschen will
        """
        logger.debug("mitglied_id={}, user={}", mitglied_id, user)
        with Session() as session:
            mitglied_db: Final = self.repo.find_by_id(
                mitglied_id=mitglied_id,
                session=session,
            )
            self._pruefe_schreibzugriff(mitglied_db, mitglied_id, user)
            if mitglied_db is None:
                return
            self.repo.delete_by_id(mitglied_id=mitglied_id, session=session)
            session.commit()

    @staticmethod
    def _pruefe_schreibzugriff(
        mitglied_db: Mitglied | None,
        mitglied_id: int,
        user: User,
    ) -> None:
        """Administratoren dürfen alles, Mitglieder nur die eigenen Daten.

        Wie beim Lesen erfährt ein Mitglied auch nicht, ob es eine fremde ID gibt:
        Für Nicht-Administratoren ist eine nicht-vorhandene ID ebenfalls verboten.

        :raises ForbiddenError: Falls der User die Daten nicht ändern darf
        """
        if Role.ADMIN in user.roles:
            return
        if mitglied_db is None or mitglied_db.email != user.email.strip().lower():
            logger.warning(
                "Schreibzugriff verweigert: mitglied_id={}, user={}",
                mitglied_id,
                user.username,
            )
            raise ForbiddenError
