"""FastAPI-Anwendung mit den Endpunkten."""

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Final

from fastapi import FastAPI, Request, Response, status
from loguru import logger

from mitglied.__about__ import __version__
from mitglied.config import dev_db_populate
from mitglied.config.dev.db_populate import db_populate
from mitglied.config.dev.db_populate_router import router as db_populate_router
from mitglied.graphql_api import graphql_router
from mitglied.problem_details import ProblemDetails
from mitglied.repository import engine
from mitglied.router import mitglied_router, mitglied_write_router
from mitglied.security import AuthorizationError, LoginError, router as auth_router
from mitglied.service import (
    EmailExistsError,
    ForbiddenError,
    NotFoundError,
    VersionOutdatedError,
)

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

app.include_router(auth_router, prefix="/auth")
app.include_router(mitglied_router, prefix="/rest")
app.include_router(mitglied_write_router, prefix="/rest")
app.include_router(graphql_router, prefix="/graphql")


@app.exception_handler(NotFoundError)
def not_found_error_handler(_request: Request, _err: NotFoundError) -> Response:
    """Errorhandler für NotFoundError.

    :param _err: NotFoundError aus der Geschäftslogik
    :return: Response mit Statuscode 404
    :rtype: Response
    """
    return ProblemDetails.create(status_code=status.HTTP_404_NOT_FOUND).to_response()


@app.exception_handler(AuthorizationError)
def authorization_error_handler(
    _request: Request,
    _err: AuthorizationError,
) -> Response:
    """Errorhandler für AuthorizationError.

    :param _err: AuthorizationError vom Extrahieren der Benutzerkennung
    :return: Response mit Statuscode 401
    :rtype: Response
    """
    return ProblemDetails.create(status_code=status.HTTP_401_UNAUTHORIZED).to_response()


@app.exception_handler(ForbiddenError)
def forbidden_error_handler(_request: Request, _err: ForbiddenError) -> Response:
    """Errorhandler für ForbiddenError.

    :param _err: ForbiddenError vom Überprüfen der erforderlichen Berechtigungen
    :return: Response mit Statuscode 403
    :rtype: Response
    """
    return ProblemDetails.create(status_code=status.HTTP_403_FORBIDDEN).to_response()


@app.exception_handler(LoginError)
def login_error_handler(_request: Request, err: LoginError) -> Response:
    """Exception-Handler, wenn der Benutzername oder das Passwort fehlerhaft ist.

    :param err: LoginError
    :return: Response-Objekt mit Statuscode 401
    :rtype: Response
    """
    return ProblemDetails.create(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=str(err),
    ).to_response()


@app.exception_handler(EmailExistsError)
def email_exists_error_handler(_request: Request, err: EmailExistsError) -> Response:
    """Exception-Handling für EmailExistsError.

    :param err: Exception, falls die Emailadresse bereits existiert
    :return: Response mit Statuscode 422
    :rtype: Response
    """
    return ProblemDetails.create(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail=str(err),
    ).to_response()


@app.exception_handler(VersionOutdatedError)
def version_outdated_error_handler(
    _request: Request,
    err: VersionOutdatedError,
) -> Response:
    """Exception-Handling für VersionOutdatedError.

    :param err: Exception, falls die Versionsnummer zum Aktualisieren veraltet ist
    :return: Response mit Statuscode 412
    :rtype: Response
    """
    return ProblemDetails.create(
        status_code=status.HTTP_412_PRECONDITION_FAILED,
        detail=str(err),
    ).to_response()


@app.get("/")
def hello() -> dict[str, str]:
    """Erster GET-Request: liefert eine Begrüßung als JSON."""
    return {"message": "Hello Fitnessstudio"}


# Neuladen der DB nur im dev-Modus anbieten
if dev_db_populate:
    app.include_router(db_populate_router, prefix="/dev")
