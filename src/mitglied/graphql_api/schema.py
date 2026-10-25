"""Schema für GraphQL durch Strawberry."""

from dataclasses import asdict
from typing import Final
lazy from collections.abc import Sequence

import strawberry
from fastapi import Request
from loguru import logger
from strawberry.extensions import PydanticErrorExtension
from strawberry.fastapi import GraphQLRouter
lazy from strawberry.types import Info

from mitglied.config.graphql import graphql_ide
from mitglied.graphql_api.graphql_types import (
    CreatePayload,
    LoginResult,
    MitgliedInput,
    Suchparameter,
)
from mitglied.repository import MitgliedRepository, MitgliedSuchparameter, Pageable
from mitglied.router.mitglied_model import MitgliedModel
from mitglied.security import Role, TokenService
from mitglied.security.dependencies import get_user_service
from mitglied.service import (
    MitgliedDTO,
    MitgliedService,
    MitgliedWriteService,
    NotFoundError,
)

__all__ = ["graphql_router"]


# Strawberry ist eine "code-first library":
# - keine Schema-Datei in SDL (schema definition language) notwendig
# - das Schema wird aus Klassen generiert, die mit z.B. @type oder @input dekoriert sind

# type Mitglied {
#     nachname: String!
# }
# input Suchparameter {...}
# type Query {
#     mitglied(mitglied_id: ID!): Mitglied!
#     mitglieder(suchparameter: Suchparameter): list[Mitglied!]!
# }


_repo: Final = MitgliedRepository()
_service: MitgliedService = MitgliedService(repo=_repo)
_token_service: Final = TokenService()


@strawberry.type  # vgl. @dataclass
class Query:
    """Queries, um Mitgliederdaten zu lesen."""

    @strawberry.field
    def mitglied(self, mitglied_id: strawberry.ID, info: Info) -> MitgliedDTO | None:
        """Daten zu einem Mitglied lesen.

        :param mitglied_id: ID des gesuchten Mitglieds
        :return: Gesuchtes Mitglied
        :rtype: Mitglied
        :raises NotFoundError: Falls kein Mitglied gefunden wurde, wird zu GraphQLError
        """
        logger.debug("mitglied_id={}", mitglied_id)

        request: Final[Request] = info.context.get("request")
        user: Final = _token_service.get_user_from_request(request=request)
        if user is None:
            return None

        try:
            mitglied_dto: Final = _service.find_by_id(
                mitglied_id=int(mitglied_id),
                user=user,
            )
        except NotFoundError:
            return None
        logger.debug("{}", mitglied_dto)
        return mitglied_dto

    @strawberry.field
    def mitglieder(
        self,
        suchparameter: Suchparameter | None,
        info: Info,
    ) -> Sequence[MitgliedDTO]:
        """Mitglieder anhand von Suchparameter suchen.

        :param suchparameter: nachname, email usw.
        :return: Die gefundenen Mitglieder
        :rtype: list[Mitglied]
        :raises NotFoundError: Falls kein Mitglied gefunden wurde, wird zu GraphQLError
        """
        logger.debug("suchparameter={}", suchparameter)

        request: Final[Request] = info.context["request"]
        user: Final = _token_service.get_user_from_request(request)
        if user is None or Role.ADMIN not in user.roles:
            return []

        suchparameter_filtered = (
            None
            if suchparameter is None
            else MitgliedSuchparameter(
                email=suchparameter.email,
                nachname=suchparameter.nachname,
            )
        )
        logger.debug("suchparameter_filtered={}", suchparameter_filtered)

        pageable: Final = Pageable(number=0, size=0)
        try:
            mitglieder_dto: Final = _service.find(
                suchparameter=suchparameter_filtered,
                pageable=pageable,
            )
        except NotFoundError:
            return []
        logger.debug("{}", mitglieder_dto)
        return mitglieder_dto.content


@strawberry.type
class Mutation:
    """Mutations, um Mitglieder anzulegen und sich einzuloggen."""

    @strawberry.mutation
    def create(self, mitglied_input: MitgliedInput) -> CreatePayload:
        """Ein neues Mitglied anlegen.

        :param mitglied_input: Daten des neuen Mitglieds
        :return: ID des neuen Mitglieds
        :rtype: CreatePayload
        :raises EmailExistsError: Falls die Emailadresse bereits existiert
        """
        logger.debug("mitglied_input={}", mitglied_input)

        # Dictionary mit Pydantic validieren
        mitglied_model: Final = MitgliedModel.model_validate(asdict(mitglied_input))

        write_service: Final = MitgliedWriteService(
            repo=_repo,
            user_service=get_user_service(),
        )
        mitglied_dto: Final = write_service.create(
            mitglied=mitglied_model.to_mitglied()
        )
        payload: Final = CreatePayload(id=mitglied_dto.id)

        logger.debug("{}", payload)
        return payload

    # Mutation, weil evtl. der Login-Zeitpunkt gespeichert wird
    @strawberry.mutation
    def login(self, username: str, password: str) -> LoginResult:
        """Einen Token zu Benutzername und Passwort ermitteln.

        :param username: Benutzername
        :param password: Passwort
        :rtype: LoginResult
        """
        token_mapping = _token_service.token(username=username, password=password)

        token = token_mapping["access_token"]
        user = _token_service.get_user_from_token(token)
        roles: Final = [role.value for role in user.roles]
        return LoginResult(
            token=token, expiresIn=str(token_mapping["expires_in"]), roles=roles
        )


schema: Final = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    extensions=[
        PydanticErrorExtension,
    ],
)


Context = dict[str, Request]


# Dependency Injection: Request von FastAPI weiterreichen an den Kontext von Strawberry
def get_context(request: Request) -> Context:
    """Request von FastAPI an den Strawberry-Kontext weiterreichen."""
    return {"request": request}


graphql_router: Final = GraphQLRouter[Context](
    schema,
    context_getter=get_context,
    graphql_ide=graphql_ide,
)
