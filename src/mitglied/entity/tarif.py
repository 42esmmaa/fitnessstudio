"""Enum für den Vertragstarif."""

from enum import StrEnum

import strawberry


@strawberry.enum
class Tarif(StrEnum):
    """Die verfügbaren Vertragstarife."""

    BASIC = "BASIC"
    """Basistarif."""

    PREMIUM = "PREMIUM"
    """Premiumtarif."""

    STUDENT = "STUDENT"
    """Studierendentarif."""
