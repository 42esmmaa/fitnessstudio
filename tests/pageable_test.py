"""Unit-Tests für Pageable.create() mit Eingaben aus Query-Parametern."""

import pytest

from mitglied.repository import (
    DEFAULT_PAGE_NUMBER,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    Pageable,
)


@pytest.mark.parametrize(
    ("number", "size", "erwartete_number", "erwartete_size"),
    [
        (None, None, DEFAULT_PAGE_NUMBER, DEFAULT_PAGE_SIZE),
        ("2", "10", 2, 10),
        ("0", "1", 0, 1),
        ("0", str(MAX_PAGE_SIZE), 0, MAX_PAGE_SIZE),
        # ungültige Werte werden durch die Defaults ersetzt
        ("-1", "-5", DEFAULT_PAGE_NUMBER, DEFAULT_PAGE_SIZE),
        ("abc", "x", DEFAULT_PAGE_NUMBER, DEFAULT_PAGE_SIZE),
        ("", "", DEFAULT_PAGE_NUMBER, DEFAULT_PAGE_SIZE),
        ("1.5", "2.5", DEFAULT_PAGE_NUMBER, DEFAULT_PAGE_SIZE),
        # hochgestellte Ziffern: "²".isdigit() ist True, int("²") wirft ValueError
        ("²", "²", DEFAULT_PAGE_NUMBER, DEFAULT_PAGE_SIZE),
        # size=0 würde im Repository ALLE Datensätze liefern
        ("0", "0", 0, DEFAULT_PAGE_SIZE),
        ("0", str(MAX_PAGE_SIZE + 1), 0, DEFAULT_PAGE_SIZE),
    ],
)
def test_create(number, size, erwartete_number, erwartete_size) -> None:
    pageable = Pageable.create(number=number, size=size)
    assert pageable.number == erwartete_number
    assert pageable.size == erwartete_size
