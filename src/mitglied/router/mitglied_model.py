"""Pydantic-Model für die Mitgliedsdaten."""

from typing import Final, override

from loguru import logger
from pydantic import ConfigDict

from mitglied.router.mitglied_update_model import MitgliedUpdateModel
lazy from mitglied.entity import Mitglied
lazy from mitglied.router.vertrag_model import VertragModel
lazy from mitglied.router.zahlung_model import ZahlungModel

__all__ = ["MitgliedModel"]


class MitgliedModel(MitgliedUpdateModel):
    """Pydantic-Model für die Mitgliedsdaten."""

    vertrag: VertragModel | None = None
    """Der optionale zugehörige Vertrag."""
    zahlungen: list[ZahlungModel]
    """Die Liste der Zahlungen."""

    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)

    @override
    def to_mitglied(self) -> Mitglied:
        """Konvertierung in ein Mitglied-Objekt für SQLAlchemy.

        :return: Mitglied-Objekt für SQLAlchemy
        :rtype: Mitglied
        """
        logger.debug("self={}", self)
        mitglied: Final = super().to_mitglied()
        mitglied.vertrag = (
            self.vertrag.to_vertrag() if self.vertrag is not None else None
        )
        mitglied.zahlungen = [
            zahlung_model.to_zahlung() for zahlung_model in self.zahlungen
        ]
        logger.debug("mitglied={}", mitglied)
        return mitglied
