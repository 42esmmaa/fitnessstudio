"""Entity-Klasse für eine Zahlung."""

from __future__ import annotations

from typing import TYPE_CHECKING
lazy from datetime import date
lazy from decimal import Decimal

from sqlalchemy import ForeignKey, Identity, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mitglied.entity.base import Base

if TYPE_CHECKING:
    from mitglied.entity.mitglied import Mitglied


class Zahlung(Base):
    """Zahlung in einer 1:N-Beziehung zu einem Mitglied."""

    __tablename__ = "zahlung"

    betrag: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    zahlungsdatum: Mapped[date]

    id: Mapped[int] = mapped_column(Identity(start=1000), primary_key=True, init=False)
    mitglied_id: Mapped[int] = mapped_column(ForeignKey("mitglied.id"), init=False)
    mitglied: Mapped[Mitglied] = relationship(
        back_populates="zahlungen", init=False, repr=False
    )
