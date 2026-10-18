"""Parameter für Pagination."""

from dataclasses import dataclass
from typing import Final

__all__ = ["DEFAULT_PAGE_NUMBER", "DEFAULT_PAGE_SIZE", "MAX_PAGE_SIZE", "Pageable"]


DEFAULT_PAGE_SIZE = 5
MAX_PAGE_SIZE = 100
DEFAULT_PAGE_NUMBER = 0


@dataclass(eq=False, slots=True, kw_only=True)
class Pageable:
    """Data class für die Parameter für Pagination."""

    size: int
    """Anzahl Datensätze pro Seite."""

    number: int
    """Seitennummer."""

    @classmethod
    def create(cls, number: str | None = None, size: str | None = None) -> Pageable:
        """Pageable-Objekt aus Eingabedaten erstellen.

        Ungültige Werte werden durch die Defaults ersetzt. Gültig sind nur Ziffern
        0-9, d.h. keine negativen Zahlen und keine Zeichen wie "²". Die Anzahl pro
        Seite muss zwischen 1 und MAX_PAGE_SIZE liegen.

        :param number: Seitennummer als String.
        :param size: Anzahl pro Seite als String.
        :return: Pageable-Objekt mit Anzahl pro Seite und Seitennummer.
        :rtype: Pageable
        """
        # isdecimal() statt isdigit(): "²".isdigit() ist True, aber int("²") scheitert
        number_int: Final = (
            int(number)
            if number is not None and number.isdecimal()
            else DEFAULT_PAGE_NUMBER
        )
        size_int: Final = (
            int(size)
            if size is not None and size.isdecimal() and 0 < int(size) <= MAX_PAGE_SIZE
            else DEFAULT_PAGE_SIZE
        )
        return cls(size=size_int, number=number_int)
