# Lasttest mit Locust

[Locust](https://locust.io) simuliert viele gleichzeitige Benutzer. Die Szenarien
stehen als Python-Code in `locustfile.py`: Ein simulierter Administrator holt
sich beim Start einen Token und sendet danach lesende Requests:

| Task             | Gewicht | Requests                                     |
| ---------------- | ------- | -------------------------------------------- |
| `get_by_id`      | 3       | `GET /rest/{id}` für alle IDs der Testdaten  |
| `get_nachname`   | 2       | `GET /rest?nachname=...`                     |
| `get_email`      | 2       | `GET /rest?email=...`                        |
| `graphql_nachname` | 1     | GraphQL-Query `mitglieder` mit Nachname      |

## Vorbereitung

1. PostgreSQL, Keycloak und Mailpit starten (siehe README im Projektverzeichnis).
2. Für aussagekräftige Messungen das Protokollieren reduzieren, z.B. in
   `src/mitglied/config/resources/app.toml` bzw. `extras/compose/mitglied/app.toml`:
   - `[db] log-statements = false`
   - `[logger] debug-level = false`
3. Appserver starten: `uv run mitglied` oder als Docker-Container.

Das Passwort für den Benutzer `admin` wird aus der lokalen Datei `.env`
(`KEYCLOAK_ADMIN_PASSWORD`) gelesen. Deshalb Locust im **Projektverzeichnis** aufrufen.

## Aufruf

```powershell
# mit Weboberflaeche unter http://localhost:8089
uv run locust -f tests/lasttest/locustfile.py --host http://127.0.0.1:8000

# ohne Weboberflaeche: 50 Benutzer, 5 neue pro Sekunde, 1 Minute
uv run locust -f tests/lasttest/locustfile.py --host http://127.0.0.1:8000 `
    --headless --users 50 --spawn-rate 5 --run-time 1m
```

In der Weboberfläche sieht man pro Endpunkt die Anzahl Requests, Fehler,
Antwortzeiten (Median, 95. Perzentil) und Requests pro Sekunde.
