"""Factory-Funktionen für Dependency Injection."""

from typing import Annotated

from fastapi import Depends

from mitglied.repository.mitglied_repository import MitgliedRepository
from mitglied.service.mitglied_service import MitgliedService
from mitglied.service.mitglied_write_service import MitgliedWriteService


def get_repository() -> MitgliedRepository:
    """Factory-Funktion für MitgliedRepository.

    :return: Das Repository
    :rtype: MitgliedRepository
    """
    return MitgliedRepository()


def get_service(
    repo: Annotated[MitgliedRepository, Depends(get_repository)],
) -> MitgliedService:
    """Factory-Funktion für MitgliedService."""
    return MitgliedService(repo=repo)


def get_write_service(
    repo: Annotated[MitgliedRepository, Depends(get_repository)],
) -> MitgliedWriteService:
    """Factory-Funktion für MitgliedWriteService."""
    return MitgliedWriteService(repo=repo)
