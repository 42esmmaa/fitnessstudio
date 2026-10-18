"""Entity-Klasse für Mitgliedsdaten."""

from typing import Self, override
lazy from datetime import date, datetime

from sqlalchemy import JSON, Identity, func
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from mitglied.entity.base import Base
lazy from mitglied.entity.geschlecht import Geschlecht
lazy from mitglied.entity.vertrag import Vertrag
lazy from mitglied.entity.zahlung import Zahlung


class Mitglied(Base):
    """Mitglied mit einem Vertrag und mehreren Zahlungen."""

    __tablename__ = "mitglied"

    vorname: Mapped[str]
    """Der Vorname."""
    nachname: Mapped[str]
    """Der Nachname."""
    email: Mapped[str] = mapped_column(unique=True)
    """Die eindeutige Emailadresse."""
    geburtsdatum: Mapped[date]
    """Das Geburtsdatum."""
    geschlecht: Mapped[Geschlecht]
    """Das Geschlecht."""
    interessen: Mapped[list[str] | None] = mapped_column(
        JSON, default=None, kw_only=True
    )
    """Die optionalen Interessen als JSON-Array mit Strings."""

    id: Mapped[int | None] = mapped_column(Identity(start=1000), primary_key=True)
    """Die generierte ID gemäß der zugehörigen IDENTITY-Spalte."""
    vertrag: Mapped[Vertrag | None] = relationship(
        back_populates=lambda: Vertrag.mitglied,
        # kein innerjoin=True: sonst fehlen Mitglieder ohne Vertrag bei joinedload()
        cascade="save-update, delete",
    )
    """Der in einer 1:1-Beziehung referenzierte Vertrag."""
    zahlungen: Mapped[list[Zahlung]] = relationship(
        back_populates=lambda: Zahlung.mitglied,
        cascade="save-update, delete",
    )
    """Die in einer 1:N-Beziehung referenzierten Zahlungen."""
    erzeugt: Mapped[datetime | None] = mapped_column(insert_default=func.now())
    """Der Zeitstempel für das initiale INSERT."""
    aktualisiert: Mapped[datetime | None] = mapped_column(
        insert_default=func.now(), onupdate=func.now()
    )
    """Der Zeitstempel vom letzten UPDATE."""
    version: Mapped[int] = mapped_column(nullable=False, default=0)
    """Die Versionsnummer für optimistische Synchronisation."""

    __mapper_args__ = {"version_id_col": version}  # ruff: ignore[mutable-class-default]

    @validates("email")
    def _normalisiere_email(self, _key: str, email: str) -> str:
        """Emailadresse vor dem Speichern in Kleinbuchstaben umwandeln.

        Damit sind z.B. "Alice@Example.org" und "alice@example.org" dieselbe
        Adresse und die UNIQUE-Bedingung greift auch bei anderer Schreibweise.
        """
        return email.strip().lower()

    def set(self, mitglied: Self) -> None:
        """Primitive Attributwerte vor einem Datenbank-Update übernehmen."""
        self.vorname = mitglied.vorname
        self.nachname = mitglied.nachname
        self.email = mitglied.email
        self.geburtsdatum = mitglied.geburtsdatum
        self.geschlecht = mitglied.geschlecht
        self.interessen = mitglied.interessen

    @override
    def __eq__(self, other: object) -> bool:
        """Mitglieder anhand ihrer ID vergleichen, ohne Joins zu verursachen."""
        if self is other:
            return True
        if not isinstance(other, type(self)):
            return False
        return self.id is not None and self.id == other.id

    # Die Dataclass-Basis hat __hash__ = None; hier wie in der Vorlage ersetzen.
    def __hash__(self) -> int:  # ty: ignore[invalid-attribute-override]
        """Hash anhand der ID berechnen, ohne Joins zu verursachen."""
        return hash(self.id) if self.id is not None else hash(type(self))

    @override
    def __repr__(self) -> str:
        """Mitglied als String ausgeben, ohne Joins zu verursachen."""
        return (
            f"Mitglied(id={self.id}, version={self.version}, "
            f"vorname={self.vorname}, nachname={self.nachname}, email={self.email}, "
            f"geburtsdatum={self.geburtsdatum}, geschlecht={self.geschlecht}, "
            f"interessen={self.interessen}, "
            f"erzeugt={self.erzeugt}, aktualisiert={self.aktualisiert})"
        )
