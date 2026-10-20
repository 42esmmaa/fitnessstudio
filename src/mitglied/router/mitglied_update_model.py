"""Pydantic-Model zum Aktualisieren von Mitgliedsdaten."""

from typing import Annotated
lazy from datetime import date

from loguru import logger
from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints

from mitglied.entity import Mitglied
lazy from mitglied.entity import Geschlecht

__all__ = ["MitgliedUpdateModel"]


class MitgliedUpdateModel(BaseModel):
    """Pydantic-Model zum Aktualisieren von Mitgliedsdaten."""

    vorname: Annotated[str, StringConstraints(max_length=64)]
    """Der Vorname."""
    nachname: Annotated[
        str,
        StringConstraints(
            pattern="^[A-ZÄÖÜ][a-zäöüß]+(-[A-ZÄÖÜ][a-zäöüß])?$",
            max_length=64,
        ),
    ]
    """Der Nachname."""
    email: EmailStr
    """Die eindeutige Emailadresse."""
    geburtsdatum: date = Field(strict=False)
    """Das Geburtsdatum. Keine strikte Validierung: String in JSON."""
    geschlecht: Geschlecht = Field(strict=False)
    """Das Geschlecht. Keine strikte Validierung: String in JSON."""
    interessen: list[str] | None = None
    """Die optionale Liste der Interessen."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "vorname": "Alex",
                "nachname": "Muster",
                "email": "alex@example.org",
                "geburtsdatum": "2000-01-01",
                "geschlecht": "D",
                "interessen": ["Yoga", "Krafttraining"],
            },
        },
        strict=True,
        extra="forbid",
        frozen=True,
    )

    def to_mitglied(self) -> Mitglied:
        """Konvertierung in ein Mitglied-Objekt für SQLAlchemy.

        :return: Mitglied-Objekt für SQLAlchemy ohne Vertrag und Zahlungen
        :rtype: Mitglied
        """
        logger.debug("self={}", self)
        mitglied = Mitglied(
            id=None,
            vorname=self.vorname,
            nachname=self.nachname,
            email=self.email,
            geburtsdatum=self.geburtsdatum,
            geschlecht=self.geschlecht,
            interessen=self.interessen,
            vertrag=None,
            zahlungen=[],
            erzeugt=None,
            aktualisiert=None,
        )
        logger.debug("mitglied={}", mitglied)
        return mitglied
