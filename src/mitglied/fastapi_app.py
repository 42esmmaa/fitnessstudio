"""FastAPI-Anwendung mit den Endpunkten."""

from typing import Final

from fastapi import FastAPI

from mitglied.__about__ import __version__

__all__ = ["app"]

app: Final = FastAPI(title="Fitnessstudio", version=__version__)


@app.get("/")
def hello() -> dict[str, str]:
    """Erster GET-Request: liefert eine Begrüßung als JSON."""
    return {"message": "Hello Fitnessstudio"}
