"""Data class für die Login-Daten."""

from dataclasses import dataclass

__all__ = ["LoginData"]


@dataclass(frozen=True, eq=False, slots=True, kw_only=True)
class LoginData:
    """Data class für die Login-Daten."""

    username: str
    """Benutzername"""
    password: str
    """Passwort"""

    class Config:
        """Beispiel für OpenAPI."""

        json_schema_extra = {  # ruff: ignore[mutable-class-default]
            "example": {
                "username": "admin",
                "password": "p",  # NOSONAR
            },
        }
