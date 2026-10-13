"""Appserver für die Mitgliederverwaltung eines Fitnessstudios."""

from mitglied.asgi_server import run
from mitglied.fastapi_app import app

__all__ = ["app", "main"]


def main() -> None:
    """Server starten mit `uv run mitglied`."""
    run()
