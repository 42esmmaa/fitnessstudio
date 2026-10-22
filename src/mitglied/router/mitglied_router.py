"""MitgliedGetRouter."""

from typing import Annotated, Final

from fastapi import APIRouter, Depends, Query, Request, Response, status
from fastapi.responses import JSONResponse
from loguru import logger

from mitglied.router.constants import ETAG, IF_NONE_MATCH, IF_NONE_MATCH_MIN_LEN
from mitglied.router.dependencies import get_service
from mitglied.router.mitglied_find_model import (
    MitgliedFindModel,
    MitgliedPageModel,
    MitgliedResponseModel,
)
from mitglied.security import Role, RolesRequired, User
lazy from mitglied.service import MitgliedService

__all__ = ["mitglied_router"]


mitglied_router: Final = APIRouter(tags=["Lesen"])


@mitglied_router.get(
    path="/{mitglied_id}",
    dependencies=[Depends(RolesRequired([Role.ADMIN, Role.MITGLIED]))],
    response_model=MitgliedResponseModel,
)
def get_by_id(
    mitglied_id: int,
    request: Request,
    service: Annotated[MitgliedService, Depends(get_service)],
) -> Response:
    """Suche mit der Mitglied-ID.

    :param mitglied_id: ID des gesuchten Mitglieds als Pfadparameter
    :param request: Injiziertes Request-Objekt von FastAPI bzw. Starlette
        mit ggf. If-None-Match im Header
    :param service: Injizierter Service für Geschäftslogik
    :return: Response mit dem gefundenen Mitgliedsdatensatz
    :rtype: Response
    :raises NotFoundError: Falls kein Mitglied gefunden wurde
    :raises ForbiddenError: Falls die Mitgliedsdaten nicht gelesen werden dürfen
    """
    # User-Objekt ist durch Depends(RolesRequired()) in Request.state gepuffert
    user: Final[User] = request.state.current_user
    logger.debug("mitglied_id={}, user={}", mitglied_id, user)

    mitglied: Final = service.find_by_id(mitglied_id=mitglied_id, user=user)
    logger.debug("{}", mitglied)

    if_none_match: Final = request.headers.get(IF_NONE_MATCH)
    if (
        if_none_match is not None
        and len(if_none_match) >= IF_NONE_MATCH_MIN_LEN
        and if_none_match.startswith('"')
        and if_none_match.endswith('"')
    ):
        version = if_none_match[1:-1]
        logger.debug("version={}", version)
        if version is not None:
            try:
                if int(version) == mitglied.version:
                    return Response(status_code=status.HTTP_304_NOT_MODIFIED)
            except ValueError:
                logger.debug("invalid version={}", version)

    mitglied_model: Final = MitgliedResponseModel.from_dto(mitglied)
    return JSONResponse(
        content=mitglied_model.model_dump(mode="json"),
        headers={ETAG: f'"{mitglied.version}"'},
    )


@mitglied_router.get(
    path="",
    dependencies=[Depends(RolesRequired(Role.ADMIN))],
    response_model=MitgliedPageModel,
)
def get(
    find_model: Annotated[MitgliedFindModel, Query()],
    service: Annotated[MitgliedService, Depends(get_service)],
) -> MitgliedPageModel:
    """Suche mit Query-Parameter.

    :param find_model: Validierte Such- und Pagination-Parameter als Pydantic-Model
    :param service: Injizierter Service für Geschäftslogik
    :return: Eine Seite mit Mitglieder-Daten
    :raises NotFoundError: Falls keine Mitglieder gefunden wurden
    """
    logger.debug("search={}", find_model)
    result: Final = _find_page(service=service, find_model=find_model)
    logger.debug("result={}", result)
    return result


@mitglied_router.api_route(
    path="/query",
    methods=["QUERY"],
    dependencies=[Depends(RolesRequired(Role.ADMIN))],
    response_model=MitgliedPageModel,
)
def query(
    find_model: MitgliedFindModel,
    service: Annotated[MitgliedService, Depends(get_service)],
) -> MitgliedPageModel:
    """Suche mit HTTP-Methode _QUERY_.

    :param find_model: Validierte Suchparameter einschließlich Pagination
        als Pydantic-Model aus dem Request-Body
    :param service: Injizierter Service für Geschäftslogik
    :return: Eine Seite mit Mitglieder-Daten
    :raises NotFoundError: Falls keine Mitglieder gefunden wurden
    """
    logger.debug("search={}", find_model)
    result: Final = _find_page(service=service, find_model=find_model)
    logger.debug("result={}", result)
    return result


def _find_page(
    service: MitgliedService,
    find_model: MitgliedFindModel,
) -> MitgliedPageModel:
    pageable: Final = find_model.to_pageable()
    mitglied_slice: Final = service.find(
        suchparameter=find_model.to_suchparameter(),
        pageable=pageable,
    )

    mitglied_models: Final = tuple(
        MitgliedResponseModel.from_dto(mitglied) for mitglied in mitglied_slice.content
    )

    total_pages: Final = (
        (mitglied_slice.total_elements + pageable.size - 1) // pageable.size
        if pageable.size > 0
        else 1
    )

    return MitgliedPageModel(
        content=mitglied_models,
        page={
            "size": pageable.size,
            "number": pageable.number,
            "total_elements": mitglied_slice.total_elements,
            "total_pages": total_pages,
        },
    )
