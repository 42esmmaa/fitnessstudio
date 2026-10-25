"""DbPopulateController."""

from typing import Annotated, Final

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import JSONResponse
from loguru import logger

from mitglied.config.dev.db_populate import DbPopulateService, get_db_populate_service
from mitglied.problem_details import ProblemDetails
from mitglied.security import Role, RolesRequired, User

__all__ = ["router"]


router: Final = APIRouter()


# "Dependency Injection" durch Depends
@router.api_route(
    path="/db_populate",
    methods=["QUERY"],
    tags=["Admin"],
    dependencies=[Depends(RolesRequired(Role.ADMIN))],
)
async def populate(
    request: Request,
    service: Annotated[DbPopulateService, Depends(get_db_populate_service)],
) -> Response:
    """Die DB mit Testdaten durch einen QUERY-Request neu laden.

    :return: JSON-Datensatz mit der Erfolgsmeldung
    :rtype: Response
    """
    body: Final = await request.body()
    if len(body) > 0:
        logger.error("Kein leerer Request-Body")
        return ProblemDetails.create(
            status_code=status.HTTP_400_BAD_REQUEST,
        ).to_response()

    current_user: Final[User] = request.state.current_user
    logger.warning(
        'REST-Schnittstelle zum Neuladen der DB aufgerufen von "{}"',
        current_user.username,
    )
    service.populate()
    return JSONResponse(content={"db_populate": "success"})
