"""Entity-Klasse für Mitgliedsdaten."""

from __future__ import annotations

from typing import TYPE_CHECKING
lazy from datetime import date, datetime

from sqlalchemy import JSON, Identity, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mitglied.entity.base import Base
lazy from mitglied.entity.geschlecht import Geschlecht

if TYPE_CHECKING:
    from mitglied.entity.vertrag import Vertrag
    from mitglied.entity.zahlung import Zahlung


class Mitglied(Base):
    """Mitglied mit einem Vertrag und mehreren Zahlungen."""

    __tablename__ = "mitglied"

    vorname: Mapped[str]
    nachname: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    geburtsdatum: Mapped[date]
    geschlecht: Mapped[Geschlecht]
    interessen: Mapped[list[str]] = mapped_column(JSON)

    id: Mapped[int] = mapped_column(Identity(start=1000), primary_key=True, init=False)
    vertrag: Mapped[Vertrag | None] = relationship(
        back_populates="mitglied",
        cascade="save-update, delete",
        default=None,
        repr=False,
    )
    zahlungen: Mapped[list[Zahlung]] = relationship(
        back_populates="mitglied",
        cascade="save-update, delete",
        default_factory=list,
        repr=False,
    )
    erzeugt: Mapped[datetime] = mapped_column(insert_default=func.now(), init=False)
    aktualisiert: Mapped[datetime] = mapped_column(
        insert_default=func.now(), onupdate=func.now(), init=False
    )
    version: Mapped[int] = mapped_column(nullable=False, default=0, init=False)

    __mapper_args__ = {"version_id_col": version}  # ruff: ignore[mutable-class-default]
