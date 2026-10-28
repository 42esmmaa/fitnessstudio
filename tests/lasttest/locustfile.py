"""Lasttest mit Locust für den laufenden Appserver.

Aufruf im Projektverzeichnis (Appserver, PostgreSQL und Keycloak laufen):

```powershell
uv run locust -f tests/lasttest/locustfile.py --host http://127.0.0.1:8000
```

Danach im Browser <http://localhost:8089> öffnen und den Test starten.
"""

from typing import Final

from dotenv import dotenv_values
from locust import HttpUser, between, task

__all__ = ["AdminUser"]

MITGLIED_IDS: Final = (1, 20, 30, 40, 50, 60, 70)
"""IDs aus den Testdaten in extras/compose/postgres/init/mitglied/csv."""

NACHNAMEN: Final = ("a", "e", "l", "Alpha", "Beta")
"""Teilstrings für die Suche nach Nachnamen."""

EMAILS: Final = (
    "admin@fitnessstudio.de",
    "alice@fitnessstudio.de",
    "bob@fitnessstudio.de",
    "carla@fitnessstudio.de",
)
"""Vorhandene Emailadressen aus den Testdaten."""

GRAPHQL_QUERY: Final = """
query($nachname: String) {
  mitglieder(suchparameter: { nachname: $nachname }) {
    id
    nachname
    email
  }
}
"""


class AdminUser(HttpUser):
    """Simulierter Administrator, der lesende REST- und GraphQL-Requests sendet."""

    # Wartezeit zwischen zwei Tasks pro simuliertem User in Sekunden
    wait_time = between(0.5, 2)

    def on_start(self) -> None:
        """Einmal pro simuliertem User: Token holen und im Header speichern."""
        # Passwort wie bei den Integrationstests aus der lokalen Datei .env
        password: Final = dotenv_values(".env").get("KEYCLOAK_ADMIN_PASSWORD")
        response: Final = self.client.request(
            method="QUERY",
            url="/auth/token",
            json={"username": "admin", "password": password},
            name="/auth/token",
        )
        response.raise_for_status()
        token: Final = response.json()["token"]
        self.client.headers.update({"Authorization": f"Bearer {token}"})

    @task(3)
    def get_by_id(self) -> None:
        """GET-Requests mit einer ID als Pfadparameter."""
        for mitglied_id in MITGLIED_IDS:
            # "name" fasst alle IDs in der Statistik zu einer Zeile zusammen
            self.client.get(f"/rest/{mitglied_id}", name="/rest/[id]")

    @task(2)
    def get_nachname(self) -> None:
        """GET-Requests mit einem Teil des Nachnamens als Query-Parameter."""
        for teil in NACHNAMEN:
            self.client.get("/rest", params={"nachname": teil}, name="/rest?nachname")

    @task(2)
    def get_email(self) -> None:
        """GET-Requests mit der Emailadresse als Query-Parameter."""
        for email in EMAILS:
            self.client.get("/rest", params={"email": email}, name="/rest?email")

    @task(1)
    def graphql_nachname(self) -> None:
        """GraphQL-Query mit einem Teil des Nachnamens."""
        for teil in NACHNAMEN:
            self.client.post(
                "/graphql",
                json={"query": GRAPHQL_QUERY, "variables": {"nachname": teil}},
                name="/graphql mitglieder",
            )
