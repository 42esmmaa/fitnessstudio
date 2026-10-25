"""GraphQL-Queries mit simulierten Services prüfen."""

import pytest

from mitglied.security import AuthorizationError, Role, User
from mitglied.service import (
    ForbiddenError,
    NotFoundError,
)

MITGLIED_ID = 1000


def test_mitglied_mit_optionalen_feldern(client, services):
    response = client.post(
        "/graphql",
        json={
            "query": (
                '{ mitglied(mitgliedId: "1000") {'
                " id geschlecht interessen vertrag { tarif } } }"
            ),
        },
    )
    assert response.json() == {
        "data": {
            "mitglied": {
                "id": 1000,
                "geschlecht": "DIVERS",
                "interessen": None,
                "vertrag": None,
            }
        }
    }
    assert services[0].find_by_id.call_args.kwargs["mitglied_id"] == MITGLIED_ID


def test_suche_ohne_begrenzung_auf_fuenf(client, services):
    daten = client.post(
        "/graphql",
        json={
            "query": '{ mitglieder(suchparameter: {nachname: "Mus"}) { id } }',
        },
    ).json()
    assert daten == {"data": {"mitglieder": [{"id": 1000}]}}
    argumente = services[0].find.call_args.kwargs
    assert argumente["suchparameter"].nachname == "Mus"
    assert argumente["pageable"].size == 0


def test_suche_nur_fuer_admin(client, services):
    services[1].get_user_from_request.return_value = User(
        username="alex",
        email="alex@example.org",
        vorname="Alex",
        nachname="Muster",
        roles=[Role.MITGLIED],
    )
    daten = client.post(
        "/graphql", json={"query": "{ mitglieder(suchparameter: null) { id } }"}
    ).json()
    assert daten == {"data": {"mitglieder": []}}
    services[0].find.assert_not_called()


def test_fehlendes_mitglied(client, services):
    services[0].find_by_id.side_effect = NotFoundError(mitglied_id=1000)
    daten = client.post(
        "/graphql", json={"query": '{ mitglied(mitgliedId: "1000") { id } }'}
    ).json()
    assert daten == {"data": {"mitglied": None}}


@pytest.mark.parametrize("fehler", [AuthorizationError, ForbiddenError])
def test_geschuetzte_einzelsuche(client, services, fehler):
    if fehler is AuthorizationError:
        services[1].get_user_from_request.side_effect = fehler
    else:
        services[0].find_by_id.side_effect = fehler
    daten = client.post(
        "/graphql", json={"query": '{ mitglied(mitgliedId: "1000") { id } }'}
    ).json()
    assert daten["data"]["mitglied"] is None
    assert daten["errors"]
