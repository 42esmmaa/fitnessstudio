"""Validierung und Entity-Konvertierung der REST-Eingabemodelle prüfen."""

from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from mitglied.entity import Tarif
from mitglied.router import VertragModel, ZahlungModel


def test_vertrag_model_to_vertrag() -> None:
    model = VertragModel.model_validate({
        "beginn": "2026-10-01",
        "monatlicher_beitrag": "29.90",
        "tarif": "STUDENT",
        "getraenkeflat": True,
    })
    vertrag = model.to_vertrag()
    assert vertrag.beginn == date(2026, 10, 1)
    assert vertrag.monatlicher_beitrag == Decimal("29.90")
    assert vertrag.tarif is Tarif.STUDENT
    assert vertrag.getraenkeflat is True
    assert vertrag.id is None
    assert vertrag.mitglied_id is None
    assert vertrag.mitglied is None


def test_zahlung_model_to_zahlung() -> None:
    model = ZahlungModel.model_validate({
        "betrag": "29.90",
        "zahlungsdatum": "2026-10-01",
    })
    zahlung = model.to_zahlung()
    assert zahlung.betrag == Decimal("29.90")
    assert zahlung.zahlungsdatum == date(2026, 10, 1)
    assert zahlung.id is None
    assert zahlung.mitglied_id is None
    assert zahlung.mitglied is None


@pytest.mark.parametrize(
    ("feld", "wert", "fehlertyp"),
    [
        ("beginn", "kein Datum", "date_from_datetime_parsing"),
        ("monatlicher_beitrag", "-0.01", "greater_than_equal"),
        ("monatlicher_beitrag", "1.234", "decimal_max_places"),
        ("monatlicher_beitrag", "10000.00", "decimal_whole_digits"),
        ("tarif", "UNBEKANNT", "enum"),
        ("getraenkeflat", "ja", "bool_type"),
        ("unbekannt", True, "extra_forbidden"),
    ],
)
def test_vertrag_model_ungueltige_eingaben(feld, wert, fehlertyp) -> None:
    daten = {
        "beginn": "2026-10-01",
        "monatlicher_beitrag": "29.90",
        "tarif": "BASIC",
        "getraenkeflat": False,
    }
    daten[feld] = wert
    with pytest.raises(ValidationError) as fehler:
        VertragModel.model_validate(daten)
    assert any(eintrag["type"] == fehlertyp for eintrag in fehler.value.errors())


@pytest.mark.parametrize(
    ("betrag", "fehlertyp"),
    [
        ("0", "greater_than"),
        ("-1", "greater_than"),
        ("1.234", "decimal_max_places"),
        ("1000000.00", "decimal_whole_digits"),
    ],
)
def test_zahlung_model_ungueltige_betraege(betrag, fehlertyp) -> None:
    with pytest.raises(ValidationError) as fehler:
        ZahlungModel.model_validate({"betrag": betrag, "zahlungsdatum": "2026-10-01"})
    assert any(eintrag["type"] == fehlertyp for eintrag in fehler.value.errors())


def test_vertrag_model_beitrag_null_erlaubt() -> None:
    model = VertragModel.model_validate({
        "beginn": "2026-10-01",
        "monatlicher_beitrag": "0",
        "tarif": "BASIC",
        "getraenkeflat": False,
    })
    assert model.monatlicher_beitrag == Decimal(0)
