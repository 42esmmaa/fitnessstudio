"""DTO-Klasse für Mitgliedsdaten, insbesondere ohne Decorators für SQLAlchemy."""

from dataclasses import dataclass
lazy from datetime import date

import strawberry

from mitglied.service.vertrag_dto import VertragDTO
lazy from mitglied.entity import Geschlecht, Mitglied

__all__ = ["MitgliedDTO"]


@dataclass(eq=False, slots=True, kw_only=True)
@strawberry.type(name="Mitglied")
class MitgliedDTO:
    """DTO-Klasse für gelesene oder gespeicherte Mitgliedsdaten: ohne ORM-Decorators."""

    id: int
    version: int
    vorname: str
    nachname: str
    email: str
    geburtsdatum: date
    geschlecht: Geschlecht
    vertrag: VertragDTO | None
    interessen: list[str] | None

    @classmethod
    def from_mitglied(cls, mitglied: Mitglied) -> MitgliedDTO:
        """Initialisierung von MitgliedDTO durch ein Entity-Objekt von Mitglied.

        :param mitglied: Mitglied-Objekt mit Decorators zu SQLAlchemy
        :return: MitgliedDTO-Objekt mit Daten aus dem Mitglied-Objekt
        :rtype: MitgliedDTO
        """
        return cls(
            id=mitglied.id if mitglied.id is not None else -1,
            version=mitglied.version,
            vorname=mitglied.vorname,
            nachname=mitglied.nachname,
            email=mitglied.email,
            geburtsdatum=mitglied.geburtsdatum,
            geschlecht=mitglied.geschlecht,
            vertrag=(
                VertragDTO.from_vertrag(mitglied.vertrag)
                if mitglied.vertrag is not None
                else None
            ),
            interessen=(
                list(mitglied.interessen) if mitglied.interessen is not None else None
            ),
        )
