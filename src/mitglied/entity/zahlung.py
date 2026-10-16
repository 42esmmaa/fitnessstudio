"""Entity-Klasse für eine Zahlung."""

from typing import override
lazy from datetime import date
lazy from decimal import Decimal

from sqlalchemy import ForeignKey, Identity
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mitglied.entity.base import Base
from mitglied.entity.mitglied import Mitglied


class Zahlung(Base):
    """Zahlung in einer 1:N-Beziehung zu einem Mitglied."""

    __tablename__ = "zahlung"

    betrag: Mapped[Decimal]
    """Der Betrag."""

    zahlungsdatum: Mapped[date]
    """Das Zahlungsdatum."""

    id: Mapped[int | None] = mapped_column(Identity(start=1000), primary_key=True)
    """Die generierte ID gemäß der zugehörigen IDENTITY-Spalte."""

    mitglied_id: Mapped[int | None] = mapped_column(ForeignKey("mitglied.id"))
    """ID des zugehörigen Mitglieds als Fremdschlüssel in der DB-Tabelle."""

    mitglied: Mapped[Mitglied | None] = relationship(back_populates=Mitglied.zahlungen)
    """Das zugehörige transiente Mitglied-Objekt."""

    @override
    def __repr__(self) -> str:
        """Zahlung als String ohne die Mitgliedsdaten ausgeben."""
        return (
            f"Zahlung(id={self.id}, betrag={self.betrag}, "
            f"zahlungsdatum={self.zahlungsdatum})"
        )
