"""GraphQL-Mutationen mit simulierten Services prüfen."""

from mitglied.entity import Geschlecht, Tarif

CREATE = "mutation($input: MitgliedInput!) { create(mitgliedInput: $input) { id } }"


def test_anlegen_ohne_interessen_und_vertrag(client, services, eingabe, mail):
    daten = client.post(
        "/graphql",
        json={
            "query": CREATE,
            "variables": {"input": eingabe},
        },
    ).json()
    assert daten == {"data": {"create": {"id": 1000}}}
    # wie bei REST wird eine Mail im Hintergrund verschickt
    mail.assert_called_once_with(services[2].create.return_value)
    mitglied = services[2].create.call_args.kwargs["mitglied"]
    assert mitglied.interessen is None
    assert mitglied.vertrag is None
    assert mitglied.geschlecht is Geschlecht.DIVERS


def test_anlegen_mit_vertrag_und_zahlung(client, services, eingabe):
    eingabe["vertrag"] = {
        "beginn": "2026-10-01",
        "monatlicherBeitrag": "29.90",
        "tarif": "STUDENT",
        "getraenkeflat": True,
    }
    eingabe["zahlungen"] = [{"betrag": "29.90", "zahlungsdatum": "2026-10-01"}]
    eingabe["interessen"] = ["Yoga"]
    daten = client.post(
        "/graphql",
        json={
            "query": CREATE,
            "variables": {"input": eingabe},
        },
    ).json()
    assert "errors" not in daten
    mitglied = services[2].create.call_args.kwargs["mitglied"]
    assert mitglied.vertrag.tarif is Tarif.STUDENT
    assert len(mitglied.zahlungen) == 1
    assert mitglied.interessen == ["Yoga"]


def test_ungueltige_email_wird_vor_speichern_abgelehnt(client, services, eingabe):
    eingabe["email"] = "keine-email"
    daten = client.post(
        "/graphql",
        json={
            "query": CREATE,
            "variables": {"input": eingabe},
        },
    ).json()
    assert daten["errors"]
    services[2].create.assert_not_called()


def test_login_mit_tatsaechlicher_tokenlaufzeit(client, services):
    daten = client.post(
        "/graphql",
        json={
            "query": (
                'mutation { login(username: "admin", password: "test") {'
                " token expiresIn roles } }"
            ),
        },
    ).json()
    assert daten == {
        "data": {
            "login": {
                "token": "test-token",
                "expiresIn": "300",
                "roles": ["ADMIN"],
            }
        }
    }
    services[1].token.assert_called_once()
    assert services[1].token.call_args.kwargs == {
        "username": "admin",
        "password": "test",
    }
