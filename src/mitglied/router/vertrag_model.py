"""Pydantic-Model für den Vertrag."""

lazy from datetime import date
lazy from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from mitglied.entity import Vertrag
lazy from mitglied.entity import Tarif

__all__ = ["VertragModel"]


class VertragModel(BaseModel):
    """Pydantic-Model für den Vertrag."""

    beginn: date = Field(strict=False)
    """Der Vertragsbeginn. Keine strikte Validierung: String in JSON."""
    monatlicher_beitrag: Decimal = Field(
        strict=False, ge=0, max_digits=6, decimal_places=2
    )
    """Der monatliche Beitrag. Keine strikte Validierung: Betrag in JSON."""
    tarif: Tarif = Field(strict=False)
    """Der Vertragstarif. Keine strikte Validierung: String in JSON."""
    getraenkeflat: bool
    """Angabe, ob die Getränkeflat enthalten ist."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "beginn": "2026-10-01",
                "monatlicher_beitrag": "29.90",
                "tarif": "STUDENT",
                "getraenkeflat": True,
            },
        },
        strict=True,
        extra="forbid",
        frozen=True,
    )

    def to_vertrag(self) -> Vertrag:
        """Konvertierung in ein Vertrag-Objekt für SQLAlchemy.

        :return: Vertrag-Objekt für SQLAlchemy
        :rtype: Vertrag
        """
        return Vertrag(
            id=None,
            beginn=self.beginn,
            monatlicher_beitrag=self.monatlicher_beitrag,
            tarif=self.tarif,
            getraenkeflat=self.getraenkeflat,
            mitglied_id=None,
            mitglied=None,
        )
