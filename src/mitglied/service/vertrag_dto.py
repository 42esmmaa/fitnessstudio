"""DTO-Klasse für den Vertrag, insbesondere ohne Decorators für SQLAlchemy."""

from dataclasses import dataclass
lazy from datetime import date
lazy from decimal import Decimal

import strawberry

lazy from mitglied.entity import Tarif, Vertrag


@dataclass(eq=False, slots=True, kw_only=True)
@strawberry.type(name="Vertrag")
class VertragDTO:
    """DTO-Klasse für den Vertrag, insbesondere ohne Decorators für SQLAlchemy."""

    beginn: date
    monatlicher_beitrag: Decimal
    tarif: Tarif
    getraenkeflat: bool

    @classmethod
    def from_vertrag(cls, vertrag: Vertrag) -> VertragDTO:
        """Initialisierung von VertragDTO durch ein Entity-Objekt von Vertrag.

        :param vertrag: Vertrag-Objekt mit Decorators für SQLAlchemy
        :return: VertragDTO-Objekt mit Daten aus dem Vertrag-Objekt
        :rtype: VertragDTO
        """
        return cls(
            beginn=vertrag.beginn,
            monatlicher_beitrag=vertrag.monatlicher_beitrag,
            tarif=vertrag.tarif,
            getraenkeflat=vertrag.getraenkeflat,
        )
