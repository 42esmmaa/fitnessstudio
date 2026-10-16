"""Modul für persistente Mitgliedsdaten."""

from mitglied.entity.base import Base
from mitglied.entity.geschlecht import Geschlecht
from mitglied.entity.tarif import Tarif

__all__ = ["Base", "Geschlecht", "Tarif"]
