"""Geschäftslogik zur Mitgliedersuche prüfen."""

from unittest.mock import create_autospec, patch

import pytest

from mitglied.repository import (
    MitgliedRepository,
    MitgliedSuchparameter,
    Pageable,
    Slice,
)
from mitglied.service import (
    MitgliedDTO,
    MitgliedService,
    NotFoundError,
)


def test_find_wandelt_daten_um_und_behaelt_gesamtzahl(mitglied) -> None:
    repo = create_autospec(MitgliedRepository, instance=True)
    gesamtzahl = 12
    repo.find.return_value = Slice(content=(mitglied,), total_elements=gesamtzahl)
    suchparameter = MitgliedSuchparameter(nachname="Muster")
    pageable = Pageable(size=1, number=0)

    with patch("mitglied.service.mitglied_service.Session") as sessions:
        session = sessions.return_value.__enter__.return_value
        ergebnis = MitgliedService(repo).find(suchparameter, pageable)
        repo.find.assert_called_once_with(
            suchparameter=suchparameter, pageable=pageable, session=session
        )
        session.commit.assert_called_once_with()
        sessions.return_value.__exit__.assert_called_once_with(None, None, None)

    assert ergebnis.total_elements == gesamtzahl
    assert len(ergebnis.content) == 1
    dto = ergebnis.content[0]
    assert isinstance(dto, MitgliedDTO)
    assert dto.id == mitglied.id
    assert dto.nachname == "Muster"
    assert dto.vertrag is None
    assert dto.interessen is None


@pytest.mark.parametrize(
    "suchparameter", [None, MitgliedSuchparameter(nachname="Fehlt")]
)
def test_find_ohne_treffer_meldet_fehler(suchparameter) -> None:
    repo = create_autospec(MitgliedRepository, instance=True)
    repo.find.return_value = Slice(content=(), total_elements=0)

    with patch("mitglied.service.mitglied_service.Session") as sessions:
        session = sessions.return_value.__enter__.return_value
        with pytest.raises(NotFoundError) as fehler:
            MitgliedService(repo).find(suchparameter, Pageable(size=5, number=0))
        assert fehler.value.suchparameter is suchparameter
        session.commit.assert_not_called()
        sessions.return_value.__exit__.assert_called_once()
