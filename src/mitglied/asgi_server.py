"""Start der FastAPI-Anwendung mit dem ASGI-Server uvicorn."""

from typing import Final

import uvicorn

__all__ = ["run"]

HOST: Final = "127.0.0.1"
PORT: Final = 8000


def run() -> None:
    """Server mit uvicorn auf http://127.0.0.1:8000 starten."""
    uvicorn.run("mitglied:app", host=HOST, port=PORT)
