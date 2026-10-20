"""Validierung und Entity-Konvertierung der REST-Eingabemodelle prüfen."""

from datetime import date
from decimal import Decimal
from json import dumps

import pytest
from pydantic import ValidationError

from mitglied.entity import Geschlecht, Tarif
from mitglied.router import (
    MitgliedFindModel,
    MitgliedModel,
    MitgliedPageModel,
    MitgliedResponseModel,
    MitgliedUpdateModel,
    VertragModel,
    ZahlungModel,
)
from mitglied.service import MitgliedDTO


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


@pytest.fixture
def mitglied_daten():
    """Mitgliedsdaten wie im JSON-Request bereitstellen."""
    return {
        "vorname": "Alex",
        "nachname": "Muster",
        "email": "Alex@Example.org",
        "geburtsdatum": "2000-01-01",
        "geschlecht": "D",
    }


@pytest.mark.parametrize("interessen", [None, [], ["Yoga"]])
def test_mitglied_update_model_to_mitglied(mitglied_daten, interessen) -> None:
    mitglied_daten["interessen"] = interessen
    model = MitgliedUpdateModel.model_validate_json(dumps(mitglied_daten))
    mitglied = model.to_mitglied()
    assert mitglied.vorname == "Alex"
    assert mitglied.nachname == "Muster"
    assert mitglied.email == "alex@example.org"
    assert mitglied.geburtsdatum == date(2000, 1, 1)
    assert mitglied.geschlecht is Geschlecht.DIVERS
    assert mitglied.interessen == interessen
    assert mitglied.id is None
    assert mitglied.erzeugt is None
    assert mitglied.aktualisiert is None
    assert mitglied.vertrag is None
    assert mitglied.zahlungen == []


def test_mitglied_model_mit_vertrag_und_zahlungen(mitglied_daten) -> None:
    mitglied_daten["vertrag"] = {
        "beginn": "2026-10-01",
        "monatlicher_beitrag": "29.90",
        "tarif": "STUDENT",
        "getraenkeflat": True,
    }
    mitglied_daten["zahlungen"] = [
        {"betrag": "29.90", "zahlungsdatum": "2026-10-01"},
    ]
    mitglied = MitgliedModel.model_validate_json(dumps(mitglied_daten)).to_mitglied()
    assert mitglied.interessen is None
    assert mitglied.vertrag is not None
    assert mitglied.vertrag.tarif is Tarif.STUDENT
    assert mitglied.vertrag.monatlicher_beitrag == Decimal("29.90")
    assert mitglied.vertrag.mitglied is mitglied
    assert len(mitglied.zahlungen) == 1
    assert mitglied.zahlungen[0].betrag == Decimal("29.90")
    assert mitglied.zahlungen[0].mitglied is mitglied


def test_mitglied_model_ohne_optionale_felder(mitglied_daten) -> None:
    mitglied_daten["zahlungen"] = []
    mitglied = MitgliedModel.model_validate(mitglied_daten).to_mitglied()
    assert mitglied.interessen is None
    assert mitglied.vertrag is None
    assert mitglied.zahlungen == []


@pytest.mark.parametrize(
    ("feld", "wert", "fehlertyp"),
    [
        ("vorname", "A" * 65, "string_too_long"),
        ("nachname", "muster", "string_pattern_mismatch"),
        ("email", "keine-email", "value_error"),
        ("geburtsdatum", "2000-13-01", "date_from_datetime_parsing"),
        ("geschlecht", "UNBEKANNT", "enum"),
        ("interessen", "Yoga", "list_type"),
        ("interessen", [42], "string_type"),
        ("unbekannt", True, "extra_forbidden"),
    ],
)
def test_mitglied_update_model_ungueltige_eingaben(
    mitglied_daten, feld, wert, fehlertyp
) -> None:
    mitglied_daten[feld] = wert
    with pytest.raises(ValidationError) as fehler:
        MitgliedUpdateModel.model_validate(mitglied_daten)
    assert any(eintrag["type"] == fehlertyp for eintrag in fehler.value.errors())


def test_mitglied_model_prueft_verschachtelte_zahlung(mitglied_daten) -> None:
    mitglied_daten["zahlungen"] = [
        {"betrag": "-1", "zahlungsdatum": "2026-10-01"},
    ]
    with pytest.raises(ValidationError) as fehler:
        MitgliedModel.model_validate(mitglied_daten)
    assert fehler.value.errors()[0]["loc"] == ("zahlungen", 0, "betrag")


def test_mitglied_find_model_query_zu_suchparametern() -> None:
    model = MitgliedFindModel.model_validate({
        "email": "alex@example.org",
        "nachname": "Mus",
        "page": "2",
        "size": "10",
    })
    pageable = model.to_pageable()
    suchparameter = model.to_suchparameter()
    assert (pageable.number, pageable.size) == (2, 10)
    assert suchparameter.email == "alex@example.org"
    assert suchparameter.nachname == "Mus"


def test_mitglied_find_model_defaults() -> None:
    model = MitgliedFindModel()
    assert (model.to_pageable().number, model.to_pageable().size) == (0, 5)
    assert model.to_suchparameter().is_empty()


@pytest.mark.parametrize(
    "daten", [{"page": -1}, {"size": -1}, {"size": 101}, {"unbekannt": "x"}]
)
def test_mitglied_find_model_ungueltige_query(daten) -> None:
    with pytest.raises(ValidationError):
        MitgliedFindModel.model_validate(daten)


@pytest.mark.parametrize("mit_vertrag", [True, False])
def test_mitglied_response_aus_dto_als_json(mitglied_daten, mit_vertrag) -> None:
    mitglied_daten["zahlungen"] = []
    if mit_vertrag:
        mitglied_daten["vertrag"] = {
            "beginn": "2026-10-01",
            "monatlicher_beitrag": "29.90",
            "tarif": "STUDENT",
            "getraenkeflat": True,
        }
    mitglied = MitgliedModel.model_validate(mitglied_daten).to_mitglied()
    mitglied.id = 1000
    dto = MitgliedDTO.from_mitglied(mitglied)
    response = MitgliedResponseModel.from_dto(dto)
    seite = MitgliedPageModel(
        content=(response,),
        page={"size": 5, "number": 0, "total_elements": 1, "total_pages": 1},
    )
    daten = seite.model_dump(mode="json")
    assert daten["page"]["total_elements"] == 1
    inhalt = daten["content"][0]
    assert inhalt["id"] == mitglied.id
    assert inhalt["geburtsdatum"] == "2000-01-01"
    assert inhalt["geschlecht"] == "D"
    assert inhalt["interessen"] is None
    if mit_vertrag:
        assert inhalt["vertrag"]["tarif"] == "STUDENT"
        assert Decimal(inhalt["vertrag"]["monatlicher_beitrag"]) == Decimal("29.90")
    else:
        assert inhalt["vertrag"] is None
