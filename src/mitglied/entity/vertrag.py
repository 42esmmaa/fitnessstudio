"""Entity-Klasse für den Mitgliedsvertrag."""

from __future__ import annotations

from typing import TYPE_CHECKING
lazy from datetime import date
lazy from decimal import Decimal

from sqlalchemy import ForeignKey, Identity, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mitglied.entity.base import Base
lazy from mitglied.entity.tarif import Tarif

if TYPE_CHECKING:
    from mitglied.entity.mitglied import Mitglied


class Vertrag(Base):
    """Vertrag in einer 1:1-Beziehung zu einem Mitglied."""

    __tablename__ = "vertrag"

    beginn: Mapped[date]
    monatlicher_beitrag: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    tarif: Mapped[Tarif]
    getraenkeflat: Mapped[bool]

    id: Mapped[int] = mapped_column(Identity(start=1000), primary_key=True, init=False)
    mitglied_id: Mapped[int] = mapped_column(
        ForeignKey("mitglied.id"), unique=True, init=False
    )
    mitglied: Mapped[Mitglied] = relationship(
        back_populates="vertrag", init=False, repr=False
    )
