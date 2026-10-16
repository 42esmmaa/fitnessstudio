"""Enum für den Vertragstarif."""

from enum import StrEnum


class Tarif(StrEnum):
    """Die verfügbaren Vertragstarife."""

    BASIC = "BASIC"
    """Basistarif."""

    PREMIUM = "PREMIUM"
    """Premiumtarif."""

    STUDENT = "STUDENT"
    """Studierendentarif."""
