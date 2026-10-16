"""Entity-Klasse für den Mitgliedsvertrag."""

from typing import override
lazy from datetime import date
lazy from decimal import Decimal

from sqlalchemy import ForeignKey, Identity
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mitglied.entity.base import Base
from mitglied.entity.mitglied import Mitglied
lazy from mitglied.entity.tarif import Tarif


class Vertrag(Base):
    """Vertrag in einer 1:1-Beziehung zu einem Mitglied."""

    __tablename__ = "vertrag"

    beginn: Mapped[date]
    """Der Vertragsbeginn."""

    monatlicher_beitrag: Mapped[Decimal]
    """Der monatliche Beitrag."""

    tarif: Mapped[Tarif]
    """Der Vertragstarif."""

    getraenkeflat: Mapped[bool]
    """Angabe, ob die Getränkeflat enthalten ist."""

    id: Mapped[int | None] = mapped_column(Identity(start=1000), primary_key=True)
    """Die generierte ID gemäß der zugehörigen IDENTITY-Spalte."""

    mitglied_id: Mapped[int | None] = mapped_column(
        ForeignKey("mitglied.id"), unique=True
    )
    """Eindeutige ID des Mitglieds als Fremdschlüssel für die 1:1-Beziehung."""

    mitglied: Mapped[Mitglied | None] = relationship(back_populates=Mitglied.vertrag)
    """Das zugehörige transiente Mitglied-Objekt."""

    @override
    def __repr__(self) -> str:
        """Vertrag als String ohne die Mitgliedsdaten ausgeben."""
        return (
            f"Vertrag(id={self.id}, beginn={self.beginn}, "
            f"monatlicher_beitrag={self.monatlicher_beitrag}, "
            f"tarif={self.tarif}, getraenkeflat={self.getraenkeflat})"
        )
