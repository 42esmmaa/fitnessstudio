"""MitgliedWriteRouter."""

from typing import Annotated, Final

from fastapi import APIRouter, BackgroundTasks, Depends, Request, Response, status
from loguru import logger

from mitglied.problem_details import ProblemDetails
from mitglied.router.constants import IF_MATCH, IF_MATCH_MIN_LEN
from mitglied.router.dependencies import get_write_service
from mitglied.security import Role, RolesRequired
from mitglied.service import send_mail
lazy from mitglied.router.mitglied_model import MitgliedModel
lazy from mitglied.router.mitglied_update_model import MitgliedUpdateModel
lazy from mitglied.service import MitgliedWriteService

__all__ = ["mitglied_write_router"]


mitglied_write_router: Final = APIRouter(tags=["Schreiben"])


@mitglied_write_router.post("")
def post(
    mitglied_model: MitgliedModel,
    request: Request,
    background_tasks: BackgroundTasks,
    service: Annotated[MitgliedWriteService, Depends(get_write_service)],
) -> Response:
    """POST-Request, um ein neues Mitglied anzulegen.

    :param mitglied_model: Mitgliedsdaten als Pydantic-Model
    :param request: Injiziertes Request-Objekt mit der Request-URL
    :param background_tasks: Hintergrundtask für den Mailversand
    :param service: Injizierter Service für Geschäftslogik
    :rtype: Response
    :raises ValidationError: Falls es bei Pydantic Validierungsfehler gibt
    :raises EmailExistsError: Falls die Emailadresse bereits existiert
    """
    logger.debug("mitglied_model={}", mitglied_model)
    mitglied_dto: Final = service.create(mitglied=mitglied_model.to_mitglied())
    logger.debug("mitglied_dto={}", mitglied_dto)

    background_tasks.add_task(send_mail, mitglied_dto)

    return Response(
        status_code=status.HTTP_201_CREATED,
        headers={"Location": f"{request.url}/{mitglied_dto.id}"},
        background=background_tasks,
    )


@mitglied_write_router.put(
    "/{mitglied_id}",
    dependencies=[Depends(RolesRequired([Role.ADMIN, Role.MITGLIED]))],
)
def put(
    mitglied_id: int,
    mitglied_update_model: MitgliedUpdateModel,
    request: Request,
    service: Annotated[MitgliedWriteService, Depends(get_write_service)],
) -> Response:
    """PUT-Request, um ein Mitglied zu aktualisieren.

    :param mitglied_id: ID des zu aktualisierenden Mitglieds als Pfadparameter
    :param request: Injiziertes Request-Objekt von FastAPI bzw. Starlette
        mit If-Match im Header
    :param service: Injizierter Service für Geschäftslogik
    :return: Response mit Statuscode 204
    :rtype: Response
    :raises ValidationError: Falls es bei Pydantic Validierungsfehler gibt
    :raises EmailExistsError: Falls die neue Emailadresse bereits
    :raises NotFoundError: Falls zur id kein Mitglied existiert
    :raises VersionOutdatedError: Falls die Versionsnummer nicht aktuell ist
    """
    if_match_value: Final = request.headers.get(IF_MATCH)
    logger.debug(
        "mitglied_id={}, if_match={}, mitglied_update_model={}",
        mitglied_id,
        if_match_value,
        mitglied_update_model,
    )

    if if_match_value is None:
        return ProblemDetails.create(
            status_code=status.HTTP_428_PRECONDITION_REQUIRED,
        ).to_response()

    if (
        len(if_match_value) < IF_MATCH_MIN_LEN
        or not if_match_value.startswith('"')
        or not if_match_value.endswith('"')
    ):
        return ProblemDetails.create(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
        ).to_response()

    version: Final = if_match_value[1:-1]
    try:
        version_int: Final = int(version)
    except ValueError:
        return Response(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
        )

    mitglied: Final = mitglied_update_model.to_mitglied()
    mitglied_modified: Final = service.update(
        mitglied=mitglied,
        mitglied_id=mitglied_id,
        version=version_int,
    )
    logger.debug("mitglied_modified={}", mitglied_modified)

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
        headers={"ETag": f'"{mitglied_modified.version}"'},
    )


@mitglied_write_router.delete(
    "/{mitglied_id}",
    dependencies=[Depends(RolesRequired([Role.ADMIN, Role.MITGLIED]))],
)
def delete_by_id(
    mitglied_id: int,
    service: Annotated[MitgliedWriteService, Depends(get_write_service)],
) -> Response:
    """DELETE-Request, um ein Mitglied anhand seiner ID zu löschen.

    :param mitglied_id: ID des zu löschenden Mitglieds
    :param service: Injizierter Service für Geschäftslogik
    :return: Response mit Statuscode 204
    :rtype: Response
    """
    logger.debug("mitglied_id={}", mitglied_id)
    service.delete_by_id(mitglied_id=mitglied_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
