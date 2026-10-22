"""REST-Schnittstelle für Login."""

from json import JSONDecodeError
from typing import Annotated, Any, Final

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import JSONResponse

from mitglied.security.dependencies import get_token_service
from mitglied.security.login_data import LoginData
lazy from mitglied.security.token_service import TokenService

__all__ = ["router"]


router: Final = APIRouter(tags=["Login"])


async def request_body_to_dict(request: Request) -> dict[str, Any]:
    """Pydantic nicht verwenden: 401 statt Validierungsfehler 422."""
    try:
        body: dict[str, Any] = await request.json()
    except JSONDecodeError:
        # auch leerer Body
        return {}
    else:
        return body


@router.api_route(path="/token", methods=["QUERY"])
def token(
    body: Annotated[dict[str, Any], Depends(request_body_to_dict)],
    service: Annotated[TokenService, Depends(get_token_service)],
) -> Response:
    """Benutzername und Passwort per QUERY-Request, um einen JWT zu erhalten.

    - **body**: Request-Body als dict durch request.json() oder {} im Fehlerfall
    """
    try:
        # Dictionary Unpacking
        login_data: Final = LoginData(**body)
    except TypeError:
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)

    if not isinstance(login_data.username, str) or not isinstance(
        login_data.password, str
    ):
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)

    token: Final = service.token(
        username=login_data.username,
        password=login_data.password,
    )
    access_token: Final = token["access_token"]
    user: Final = service.get_user_from_token(token=access_token)

    response_body: Final = {
        "token": access_token,
        "expires_in": token["expires_in"],
        "rollen": user.roles,
    }

    return JSONResponse(content=response_body)
