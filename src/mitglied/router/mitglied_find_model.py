"""Pydantic-Modelle für das Lesen von Mitgliedsdaten."""

from typing import Annotated
lazy from datetime import date
lazy from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from mitglied.repository import (
    DEFAULT_PAGE_NUMBER,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    MitgliedSuchparameter,
    Pageable,
)
lazy from mitglied.entity import Geschlecht, Tarif
lazy from mitglied.service import MitgliedDTO

__all__ = ["MitgliedFindModel", "MitgliedPageModel", "MitgliedResponseModel"]


class MitgliedFindModel(BaseModel):
    """Suchparameter und Pagination für die Mitgliedersuche."""

    email: str | None = None
    nachname: str | None = None
    page: Annotated[int, Field(ge=DEFAULT_PAGE_NUMBER)] = DEFAULT_PAGE_NUMBER
    # ge=1: size=0 bedeutet im Repository "ohne LIMIT" und darf deshalb nicht von
    # aussen kommen, sonst koennte man mit ?size=0 alle Datensaetze abfragen
    size: Annotated[int, Field(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE

    model_config = ConfigDict(extra="forbid", frozen=True)

    def to_pageable(self) -> Pageable:
        """Erzeugt die Pagination-Daten aus den validierten Parametern."""
        return Pageable(number=self.page, size=self.size)

    def to_suchparameter(self) -> MitgliedSuchparameter:
        """Erzeugt Suchparameter für den Service."""
        return MitgliedSuchparameter(email=self.email, nachname=self.nachname)


class VertragResponseModel(BaseModel):
    """Vertrag als Teil eines Model-Objekts für Mitglieder als Response.

    ConfigDict(from_attributes=True) übernimmt die Attribute von VertragDTO.
    """

    beginn: date
    monatlicher_beitrag: Decimal
    tarif: Tarif
    getraenkeflat: bool

    model_config = ConfigDict(from_attributes=True, strict=True, extra="forbid")


class MitgliedResponseModel(BaseModel):
    """Pydantic-Modell für ein gefundenes Mitglied.

    FastAPI konvertiert die Felder in JSON, z.B. date als String und Enums als Werte.
    """

    id: int
    vorname: str
    nachname: str
    email: str
    geburtsdatum: date
    geschlecht: Geschlecht
    vertrag: VertragResponseModel | None
    interessen: list[str] | None

    model_config = ConfigDict(from_attributes=True, strict=True, extra="forbid")

    @classmethod
    def from_dto(cls, mitglied: MitgliedDTO) -> MitgliedResponseModel:
        """Konvertiert ein MitgliedDTO in ein Pydantic-Modell für einen Response.

        ConfigDict(from_attributes=True) übernimmt die Attributwerte aus dem DTO.
        """
        return cls.model_validate(mitglied)


class PageMetaModel(BaseModel):
    """Metadaten für eine Page mit Mitgliedsdaten."""

    size: int
    number: int
    total_elements: int
    total_pages: int


class MitgliedPageModel(BaseModel):
    """Pydantic-Modell für einen Response bei einer Suche mit Pagination."""

    content: tuple[MitgliedResponseModel, ...]
    page: PageMetaModel
