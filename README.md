# Fitnessstudio

Appserver für die Mitgliederverwaltung eines Fitnessstudios, entwickelt mit
[FastAPI](https://fastapi.tiangolo.com) im Rahmen der Vorlesung
_Software Engineering_ an der Hochschule Karlsruhe.

## Team

| Name            | E-Mail           |
| --------------- | ---------------- |
| Esma Ak         | akes1011@h-ka.de |
| Eyübhan Yörümez | yoey1011@h-ka.de |

## Inhalt

- [Projektstand](#projektstand)
- [Voraussetzungen](#voraussetzungen)
- [Datenbank (PostgreSQL)](#datenbank-postgresql)
- [Keycloak](#keycloak)
- [Installation und Start](#installation-und-start)
- [Codeanalyse, Formatierung, Typprüfung und Tests](#codeanalyse-formatierung-typprüfung-und-tests)
- [Endpunkte](#endpunkte)
- [Projektstruktur](#projektstruktur)
- [Datenmodell](#datenmodell)
- [Technologien](#technologien)
- [Projektplan](#projektplan)

## Projektstand

- ✅ Issue #1 _Server_: Projektstruktur, `pyproject.toml`, uv, ruff, ty und
  pytest sind eingerichtet. Der Server beantwortet einen ersten GET-Request.
- ✅ Entities `Mitglied`, `Vertrag` (1:1) und `Zahlung` (1:N) mit SQLAlchemy
- ✅ Issue #3 _Datenbank_: PostgreSQL per Docker Compose, SQL-Skripte
  `create.sql`/`drop.sql`, Repository mit Suchparametern, Pagination und
  Fetch-Join, Testdaten als CSV und Neuladen der DB per REST
- ✅ Issue #4 _Keycloak_: Container per Docker Compose mit eigener Datenbank
  `keycloak` in PostgreSQL, Realm `fitnessstudio` mit Client, Rollen und
  Testbenutzern wird beim Start importiert
- Alle weiteren Funktionen sind im [Projektplan](#projektplan) erfasst.

## Voraussetzungen

- [Python](https://www.python.org) 3.15
- [uv](https://docs.astral.sh/uv) als Package- und Projekt-Manager
- [Git](https://git-scm.com)
- [VS Code](https://code.visualstudio.com) mit den Extensions _Python_, _Ruff_
  und _ty_ (empfohlen)

## Datenbank (PostgreSQL)

### Passwörter in `.env`

Passwörter stehen **nicht** im Repository. Jedes Teammitglied legt einmalig
eine lokale Datei `.env` im Projektverzeichnis an (steht in `.gitignore`):

```powershell
Copy-Item .env.example .env
# danach in .env die Passwörter eintragen; im Team nur lokal austauschen
```

Die Datei wird von Docker Compose (`env_file`) und vom Appserver
([python-dotenv](https://github.com/theskumar/python-dotenv)) gelesen.

### Container starten

PostgreSQL läuft als Docker-Container. Beim **ersten** Start (leeres Volume)
legt der Container mit den Skripten in `extras/compose/postgres/init/mitglied/sql`
den DB-User `mitglied`, die DB `mitglied` und das Schema `mitglied` an.

```shell
cd extras/compose/postgres
docker compose up      # Server starten
docker compose down    # Server herunterfahren, Daten bleiben erhalten
docker compose down -v # zusätzlich das Volume löschen, d.h. beim nächsten Start neu anlegen
```

Die Tabellen legt der **Appserver** an: Ist in
`src/mitglied/config/resources/app.toml` `db-populate = true` gesetzt, führt er
beim Start `drop.sql` und `create.sql` aus und lädt danach die CSV-Dateien aus
`extras/compose/postgres/init/mitglied/csv` per `COPY` in die Tabellen.
Im laufenden Betrieb geht das auch mit `POST /dev/db_populate`.

Im selben Container liegt auch die Datenbank `keycloak` für Keycloak
(Skript `create-keycloak-db.sh`, siehe [Keycloak](#keycloak)).

DB-User der Anwendung ist `mitglied`, der Superuser ist `postgres`. Die
Passwörter stehen in der lokalen `.env`. Wird ein Passwort nachträglich
geändert, muss das Volume neu angelegt werden (`docker compose down -v`), weil
die Init-Skripte nur beim ersten Start laufen.

## Keycloak

Keycloak läuft als Docker-Container mit eigener Datenbank `keycloak` im
PostgreSQL-Container. Realm `fitnessstudio`, Client `fitnessstudio-client`,
die Rollen `admin` und `mitglied` sowie Testbenutzer werden beim ersten Start
automatisch angelegt.

```shell
cd extras/compose/keycloak
docker compose up      # startet PostgreSQL mit
```

Admin-Konsole: <https://localhost:8843> bzw. <http://localhost:8880>, Details
in [extras/compose/keycloak/ReadMe.md](extras/compose/keycloak/ReadMe.md).

## Installation und Start

```shell
git clone https://github.com/42esmmaa/fitnessstudio.git
cd fitnessstudio

# virtuelle Umgebung .venv anlegen und alle Abhängigkeiten installieren
uv sync

# Passwörter: .env aus der Vorlage anlegen (siehe Abschnitt Datenbank)
Copy-Item .env.example .env

# Server starten
uv run mitglied

# alternativ mit automatischem Neustart bei Dateiänderungen
uv run fastapi dev
```

Danach ist der Server unter <http://127.0.0.1:8000> erreichbar. Die
automatisch erzeugte API-Dokumentation von FastAPI gibt es unter
<http://127.0.0.1:8000/docs>.

## Codeanalyse, Formatierung, Typprüfung und Tests

```shell
uv run ruff check src tests          # Codeanalyse
uv run ruff check --fix src tests    # Befunde automatisch beheben
uv run ruff format src tests         # Formatierung
uv run ty check                      # Typprüfung
uv run pytest                        # Tests mit Testabdeckung
```

`uv run pytest` erzeugt zusätzlich einen Testbericht (`report.html`) und
einen Bericht zur Testabdeckung (`htmlcov/index.html`).

Die Konfiguration aller Werkzeuge steht in `pyproject.toml`.

## Endpunkte

| Methode | Pfad | Beschreibung                                  |
| ------- | ---- | --------------------------------------------- |
| GET     | `/`  | Liefert `{"message": "Hello Fitnessstudio"}` |
| POST    | `/dev/db_populate` | DB mit den Testdaten neu laden (nur im dev-Modus) |

## Projektstruktur

```text
fitnessstudio
├── pyproject.toml          Projektdaten, Abhängigkeiten, Konfiguration der Werkzeuge
├── uv.lock                 exakte Versionen aller Abhängigkeiten
├── extras
│   └── compose
│       ├── keycloak        compose.yml, Realm-Import, TLS-Zertifikat, ReadMe.md
│       └── postgres        compose.yml, Init-Skripte für DB/Schema, CSV-Testdaten
├── .env.example            Vorlage für die lokale .env mit den Passwörtern
├── src
│   └── mitglied
│       ├── __init__.py     Einstiegspunkt main() für "uv run mitglied"
│       ├── __main__.py     Aufruf mit "python -m mitglied"
│       ├── __about__.py    Versionsnummer
│       ├── asgi_server.py  Start von uvicorn
│       ├── fastapi_app.py  FastAPI-App mit den Endpunkten und lifespan
│       ├── config          app.toml einlesen, DB-URLs, dev-Modus
│       │   ├── dev         Neuladen der DB (Service und Router)
│       │   └── resources   app.toml, postgresql/create.sql und drop.sql
│       ├── entity          Entity-Klassen für SQLAlchemy
│       └── repository      DB-Zugriff, Session-Factory, Suchparameter, Pagination
└── tests
    ├── hello_test.py       erster Test mit dem TestClient von FastAPI
    ├── entity_test.py      Entities und Repository mit SQLite im Arbeitsspeicher
    └── db_populate_test.py Zerlegen der SQL-Skripte
```

## Datenmodell

- **Mitglied**: Vorname, Nachname, E-Mail (eindeutig), Geburtsdatum,
  Geschlecht, Interessen (JSON-Array), Version, Zeitstempel
- **Vertrag**: 1:1 zum Mitglied; Beginn, monatlicher Beitrag, Tarif
  (`BASIC`, `PREMIUM`, `STUDENT`), Getränkeflat
- **Zahlung**: 1:N zum Mitglied; Betrag, Zahlungsdatum

Das ER-Diagramm wird noch ergänzt.

## Technologien

| Bereich                   | Technologie                        | Status  |
| ------------------------- | ---------------------------------- | ------- |
| Web-Framework             | FastAPI, uvicorn                   | ✅      |
| Projekt-Manager           | uv                                 | ✅      |
| Codeanalyse, Formatierung | ruff                               | ✅      |
| Typprüfung                | ty                                 | ✅      |
| Tests                     | pytest, pytest-cov, pytest-html    | ✅      |
| Validierung               | pydantic                           | geplant |
| OR-Mapping, Datenbank     | SQLAlchemy, psycopg, PostgreSQL    | ✅      |
| GraphQL                   | Strawberry                         | geplant |
| Security (OIDC, OAuth 2)  | Keycloak                           | geplant |
| Lasttests                 | Locust                             | geplant |
| Container                 | Docker Compose (PostgreSQL)        | ✅      |
| Docker-Image Appserver    | Docker                             | geplant |
| CI                        | GitHub Actions                     | geplant |
| API-Tests                 | Bruno                              | geplant |

## Projektplan

Aufgaben und Fortschritt werden im
[GitHub Project](https://github.com/users/42esmmaa/projects/1) zu diesem
Repository verwaltet.
