"""AppServer für ein Fitnessstudio."""

from fitness.asgi_server import run
from fitness.fastapi_app import app

__all__ = ["app", "main"]

def main () -> None:
    """Server starten: 'uv run fitness'."""
    run()