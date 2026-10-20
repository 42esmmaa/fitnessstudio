"""Entity-Klasse für Benutzerdaten."""

from dataclasses import dataclass

lazy from mitglied.security.role import Role


@dataclass(frozen=True, eq=False, slots=True, kw_only=True)
class User:
    """Entity-Klasse für Benutzerdaten."""

    username: str
    """Benutzername."""

    email: str
    """Emailadresse."""

    nachname: str
    """Nachname."""

    vorname: str
    """Vorname."""

    roles: list[Role]
    """Rollen als Liste von Enums."""

    password: str | None = None
    """Passwort."""
