"""Pydantic-Model für die Zahlung."""

lazy from datetime import date
lazy from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from mitglied.entity import Zahlung

__all__ = ["ZahlungModel"]


class ZahlungModel(BaseModel):
    """Pydantic-Model für die Zahlung."""

    betrag: Decimal = Field(strict=False, gt=0, max_digits=8, decimal_places=2)
    """Der Betrag. Keine strikte Validierung: Betrag in JSON."""
    zahlungsdatum: date = Field(strict=False)
    """Das Zahlungsdatum. Keine strikte Validierung: String in JSON."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "betrag": "29.90",
                "zahlungsdatum": "2026-10-01",
            },
        },
        strict=True,
        extra="forbid",
        frozen=True,
    )

    def to_zahlung(self) -> Zahlung:
        """Konvertierung in ein Zahlung-Objekt für SQLAlchemy.

        :return: Zahlung-Objekt für SQLAlchemy
        :rtype: Zahlung
        """
        return Zahlung(
            id=None,
            betrag=self.betrag,
            zahlungsdatum=self.zahlungsdatum,
            mitglied_id=None,
            mitglied=None,
        )
