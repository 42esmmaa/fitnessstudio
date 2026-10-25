"""Schema für GraphQL."""

lazy from datetime import date
lazy from decimal import Decimal

import strawberry

lazy from mitglied.entity import Geschlecht, Tarif

__all__ = [
    "CreatePayload",
    "LoginResult",
    "MitgliedInput",
    "Suchparameter",
    "VertragInput",
    "ZahlungInput",
]


@strawberry.input
class Suchparameter:
    """Suchparameter für die Suche nach Mitgliedern."""

    nachname: str | None = None
    """Nachname als Suchkriterium."""
    email: str | None = None
    """Emailadresse als Suchkriterium."""


@strawberry.input
class VertragInput:
    """Vertrag eines neuen Mitglieds."""

    beginn: date
    """Vertragsbeginn."""
    monatlicher_beitrag: Decimal
    """Monatlicher Beitrag."""
    tarif: Tarif
    """Tarif des Vertrags."""
    getraenkeflat: bool
    """Angabe, ob eine Getränkeflat gebucht ist."""


@strawberry.input
class ZahlungInput:
    """Zahlung zu einem neuen Mitglied."""

    betrag: Decimal
    """Betrag."""
    zahlungsdatum: date
    """Datum der Zahlung."""


@strawberry.input
class MitgliedInput:
    """Daten für ein neues Mitglied."""

    vorname: str
    """Vorname."""
    nachname: str
    """Nachname."""
    email: str
    """Emailadresse und Benutzername."""
    geburtsdatum: date
    """Geburtsdatum."""
    geschlecht: Geschlecht
    """Geschlecht."""
    interessen: list[str] | None = None
    """Optionale Interessen."""
    vertrag: VertragInput | None = None
    """Optionaler Vertrag."""
    zahlungen: list[ZahlungInput]
    """Zahlungen."""


@strawberry.type
class CreatePayload:
    """Resultat-Typ, wenn ein neues Mitglied angelegt wurde."""

    id: int
    """ID des neu angelegten Mitglieds."""


@strawberry.type
class LoginResult:
    """Resultat-Typ, wenn ein Login erfolgreich war."""

    token: str
    """Token des eingeloggten Users."""
    expiresIn: str  # ruff: ignore[mixed-case-variable-in-class-scope]
    """Gültigkeitsdauer des Tokens in Sekunden."""
    roles: list[str]
    """Rollen des eingeloggten Users."""
