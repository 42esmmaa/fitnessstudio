"""Basisklasse für Entity-Klassen."""

from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass


class Base(MappedAsDataclass, DeclarativeBase):
    """Basisklasse für Entity-Klassen als dataclass."""
