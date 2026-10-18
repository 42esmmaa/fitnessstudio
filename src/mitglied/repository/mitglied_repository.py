"""Repository fuer persistente Mitgliedsdaten."""

from typing import Final

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from mitglied.entity import Mitglied
from mitglied.repository.slice import Slice
lazy from mitglied.repository.mitglied_suchparameter import MitgliedSuchparameter
lazy from mitglied.repository.pageable import Pageable

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

    def find(
        self,
        suchparameter: MitgliedSuchparameter | None,
        pageable: Pageable,
        session: Session,
    ) -> Slice[Mitglied]:
        """Suche mit Suchparameter.

        :param suchparameter: Suchparameter oder None
        :param pageable: Anzahl Datensätze und Seitennummer
        :param session: Session für SQLAlchemy
        :return: Tupel, d.h. readonly Liste, der gefundenen Mitglieder oder leeres Tupel
        :rtype: Slice[Mitglied]
        """
        log_str: Final = "{}"
        logger.debug(log_str, suchparameter)
        if suchparameter is None or suchparameter.is_empty():
            return self._find_all(pageable=pageable, session=session)

        if suchparameter.email is not None:
            mitglied = self._find_by_email(email=suchparameter.email, session=session)
            logger.debug(log_str, mitglied)
            return (
                Slice(content=(mitglied,), total_elements=1)
                if mitglied is not None
                else Slice(content=(), total_elements=0)
            )

        if suchparameter.nachname is not None:
            mitglieder = self._find_by_nachname(
                teil=suchparameter.nachname,
                pageable=pageable,
                session=session,
            )
            logger.debug(log_str, mitglieder)
            return mitglieder

        return Slice(content=(), total_elements=0)

    def _find_all(self, pageable: Pageable, session: Session) -> Slice[Mitglied]:
        # ORDER BY ist bei LIMIT/OFFSET noetig: ohne Sortierung liefert die DB die
        # Datensaetze in beliebiger Reihenfolge und die Seiten koennten sich ueberlappen
        logger.debug("aufgerufen")
        offset = pageable.number * pageable.size
        statement: Final = (
            (
                select(Mitglied)
                .options(joinedload(Mitglied.vertrag))
                .order_by(Mitglied.id)
                .limit(pageable.size)
                .offset(offset)
            )
            if pageable.size != 0
            else (
                select(Mitglied)
                .options(joinedload(Mitglied.vertrag))
                .order_by(Mitglied.id)
            )
        )
        mitglieder: Final = (session.scalars(statement)).all()
        anzahl: Final = self._count_all_rows(session)
        mitglied_slice: Final = Slice(content=tuple(mitglieder), total_elements=anzahl)
        logger.debug("mitglied_slice={}", mitglied_slice)
        return mitglied_slice

    def _count_all_rows(self, session: Session) -> int:
        statement: Final = select(func.count()).select_from(Mitglied)
        count: Final = session.execute(statement).scalar()
        return count if count is not None else 0

    def _find_by_email(self, email: str, session: Session) -> Mitglied | None:
        """Ein Mitglied anhand der Emailadresse suchen.

        :param email: Emailadresse
        :param session: Session für SQLAlchemy
        :return: Gefundenes Mitglied, falls es ein Mitglied gibt, sonst None
        :rtype: Mitglied | None
        """
        logger.debug("email={}", email)  # NOSONAR
        statement: Final = (
            select(Mitglied)
            .options(joinedload(Mitglied.vertrag))
            .where(Mitglied.email == email)
        )
        mitglied: Final = session.scalar(statement)
        logger.debug("{}", mitglied)
        return mitglied

    def _find_by_nachname(
        self,
        teil: str,
        pageable: Pageable,
        session: Session,
    ) -> Slice[Mitglied]:
        logger.debug("teil={}", teil)
        offset = pageable.number * pageable.size
        statement: Final = (
            (
                select(Mitglied)
                .options(joinedload(Mitglied.vertrag))
                .filter(Mitglied.nachname.ilike(f"%{teil}%"))
                .order_by(Mitglied.id)
                .limit(pageable.size)
                .offset(offset)
            )
            if pageable.size != 0
            else (
                select(Mitglied)
                .options(joinedload(Mitglied.vertrag))
                .filter(Mitglied.nachname.ilike(f"%{teil}%"))
                .order_by(Mitglied.id)
            )
        )
        mitglieder: Final = session.scalars(statement).all()
        anzahl: Final = self._count_rows_nachname(teil, session)
        mitglied_slice: Final = Slice(content=tuple(mitglieder), total_elements=anzahl)
        logger.debug("{}", mitglied_slice)
        return mitglied_slice

    def _count_rows_nachname(self, teil: str, session: Session) -> int:
        statement: Final = (
            select(func.count())
            .select_from(Mitglied)
            .filter(Mitglied.nachname.ilike(f"%{teil}%"))
        )
        count: Final = session.execute(statement).scalar()
        return count if count is not None else 0

    def exists_email(self, email: str, session: Session) -> bool:
        """Abfrage, ob es die Emailadresse bereits gibt.

        :param email: Emailadresse
        :param session: Session für SQLAlchemy
        :return: True, falls es die Emailadresse bereits gibt, False sonst
        :rtype: bool
        """
        logger.debug("email={}", email)

        statement: Final = select(func.count()).where(Mitglied.email == email)
        anzahl: Final = session.scalar(statement)
        logger.debug("anzahl={}", anzahl)
        return anzahl is not None and anzahl > 0

    def exists_email_other_id(
        self,
        email: str,
        mitglied_id: int,
        session: Session,
    ) -> bool:
        """Abfrage, ob es die Emailadresse bei einer anderen Mitglied-ID bereits gibt.

        :param email: Emailadresse
        :param mitglied_id: eigene Mitglied-ID
        :param session: Session für SQLAlchemy
        :return: True, falls es die Emailadresse bereits gibt, False sonst
        :rtype: bool
        """
        logger.debug("email={}", email)

        statement: Final = select(Mitglied.id).where(Mitglied.email == email)
        id_db: Final = session.scalar(statement)
        logger.debug("id_db={}", id_db)
        return id_db is not None and id_db != mitglied_id
