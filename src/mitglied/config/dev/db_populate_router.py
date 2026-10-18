"""REST-Schnittstelle zum Neuladen der DB im dev-Modus."""

from typing import Annotated, Final

from fastapi import APIRouter, Depends
from loguru import logger

from mitglied.config.dev.db_populate import DbPopulateService, get_db_populate_service

__all__ = ["router"]

router: Final = APIRouter(tags=["Dev"])


# TODO Nach Keycloak (Issue Security) nur noch mit der Rolle ADMIN erlauben.
@router.post("/db_populate")
def populate(
    service: Annotated[DbPopulateService, Depends(get_db_populate_service)],
) -> dict[str, str]:
    """Die DB mit den Testdaten neu laden.

    :param service: Injizierter Service zum Neuladen der DB
    :return: JSON-Objekt mit der Erfolgsmeldung
    :rtype: dict[str, str]
    """
    logger.warning("REST-Schnittstelle zum Neuladen der DB aufgerufen")
    service.populate()
    return {"db_populate": "success"}
