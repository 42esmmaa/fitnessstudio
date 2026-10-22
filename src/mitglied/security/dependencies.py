"""Factory-Funktionen für Dependency Injection."""

from functools import cache

from mitglied.security.token_service import TokenService
from mitglied.security.user_service import UserService

_token_service = TokenService()  # Singleton-Objekt


def get_token_service() -> TokenService:
    """Factory-Funktion für TokenService."""
    return _token_service


@cache
def get_user_service() -> UserService:
    """Factory-Funktion für UserService, als Singleton beim ersten Zugriff."""
    return UserService()
