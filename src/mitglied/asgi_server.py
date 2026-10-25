"""Start der FastAPI-Anwendung mit dem ASGI-Server uvicorn."""

import uvicorn

from mitglied.config import host_binding, port

__all__ = ["run"]


def run() -> None:
    """Server mit uvicorn und der konfigurierten Adresse starten."""
    uvicorn.run("mitglied:app", host=host_binding, port=port)
