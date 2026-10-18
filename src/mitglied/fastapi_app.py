"""FastAPI-Anwendung mit den Endpunkten."""

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Final

from fastapi import FastAPI
from loguru import logger

from mitglied.__about__ import __version__
from mitglied.config import dev_db_populate
from mitglied.config.dev.db_populate import db_populate
from mitglied.config.dev.db_populate_router import router as db_populate_router
from mitglied.repository import engine

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

__all__ = ["app"]


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    """Code beim Hochfahren (vor `yield`) und Herunterfahren (nach `yield`)."""
    db_populate()
    logger.info("Server ist gestartet")
    try:
        yield
    finally:
        # DB-Verbindungen im Pool auch bei einem Fehler schliessen
        engine.dispose()
        logger.info("Server ist heruntergefahren")


app: Final = FastAPI(title="Fitnessstudio", version=__version__, lifespan=lifespan)


@app.get("/")
def hello() -> dict[str, str]:
    """Erster GET-Request: liefert eine Begrüßung als JSON."""
    return {"message": "Hello Fitnessstudio"}


# Neuladen der DB nur im dev-Modus anbieten
if dev_db_populate:
    app.include_router(db_populate_router, prefix="/dev")
