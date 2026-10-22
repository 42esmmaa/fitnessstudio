"""ProblemDetails gemäß RFC 7807."""

from dataclasses import asdict, dataclass
from typing import Any

from fastapi.responses import JSONResponse
lazy from fastapi import Response

__all__ = ["ProblemDetails"]

BAD_REQUEST = 400
UNAUTHORIZED = 401
FORBIDDEN = 403
PRECONDITION_FAILED = 412
UNPROCESSABLE_CONTENT = 422
PRECONDITION_REQUIRED = 428


@dataclass(frozen=True, eq=False, slots=True, kw_only=True)
class ProblemDetails:
    """Datenstruktur für ProblemDetails gemäß RFC 7807."""

    title: str
    status_code: int
    detail: list[dict[str, Any]] | str | None

    @classmethod
    def create(  # ruff: ignore[too-many-return-statements]
        cls,
        status_code: int,
        detail: list[dict[str, Any]] | str | None = None,
    ) -> ProblemDetails:
        """ProblemDetails gemäß RFC 7807 erstellen."""
        match status_code:
            case 400:
                return cls(title="Bad Request", status_code=status_code, detail=detail)
            case 401:
                return cls(title="Unauthorized", status_code=status_code, detail=detail)
            case 403:
                return cls(title="Forbidden", status_code=status_code, detail=detail)
            case 412:
                return cls(
                    title="Precondition Failed",
                    status_code=status_code,
                    detail=detail,
                )
            case 422:
                return cls(
                    title="Unprocessable Content",
                    status_code=status_code,
                    detail=detail,
                )
            case 428:
                return cls(
                    title="Precondition Required",
                    status_code=status_code,
                    detail=detail,
                )
            case _:
                return cls(title="Client Error", status_code=status_code, detail=detail)

    def to_response(self) -> Response:
        """ProblemDetails als Response zurückgeben.

        :return: Response mit ProblemDetails als JSON-Datensatz.
        :rtype: Response
        """
        return JSONResponse(
            status_code=self.status_code,
            content=asdict(obj=self),
            media_type="application/problem+json",
        )
