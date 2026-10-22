"""MitgliedGetRouter."""

from typing import Annotated, Final

from fastapi import APIRouter, Depends, Query
from loguru import logger

from mitglied.router.dependencies import get_service
from mitglied.router.mitglied_find_model import (
    MitgliedFindModel,
    MitgliedPageModel,
    MitgliedResponseModel,
)
from mitglied.security import Role, RolesRequired
lazy from mitglied.service import MitgliedService

__all__ = ["mitglied_router"]


mitglied_router: Final = APIRouter(tags=["Lesen"])


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
