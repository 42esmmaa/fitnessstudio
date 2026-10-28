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
- [Backend starten](#backend-starten)
- [Installation und Start](#installation-und-start)
- [Docker und CI](#docker-und-ci)
- [Codeanalyse, Formatierung, Typprüfung und Tests](#codeanalyse-formatierung-typprüfung-und-tests)
- [Bruno](#bruno)
- [Lasttest mit Locust](#lasttest-mit-locust)
- [Endpunkte](#endpunkte)
- [Projektstruktur](#projektstruktur)
- [Datenmodell](#datenmodell)
- [Dokumentation](#dokumentation)
- [Weitere Werkzeuge](#weitere-werkzeuge)
- [Technologien](#technologien)
- [Projektplan](#projektplan)

## Projektstand

Alle Anforderungen von Aufgabe 1 sind umgesetzt:

- ✅ REST-Schnittstelle mit Suche, Pagination, `ETag`/`If-Match` und Problem Details
- ✅ Validierung mit Pydantic
- ✅ OR-Mapping mit SQLAlchemy für PostgreSQL (Mitglied, Vertrag 1:1, Zahlung 1:N)
- ✅ GraphQL mit Strawberry
- ✅ Security mit Keycloak (OIDC, OAuth 2), Rollen `admin` und `mitglied`
- ✅ Mailversand an Mailpit bei der Neuanlage
- ✅ uv, ruff, ty, pytest (Unit- und Integrationstests)
- ✅ Docker-Image, Docker Compose und GitHub Actions
- ✅ Bruno, Locust, Library Skills, OWASP Dependency Check
- ✅ Dokumentation mit AsciiDoctor und PlantUML sowie mkdocs

Der Projektplan steht im [GitHub Project](https://github.com/users/42esmmaa/projects/1).

## Voraussetzungen

- [Python](https://www.python.org) 3.15
- [uv](https://docs.astral.sh/uv) als Package- und Projekt-Manager
- [Docker](https://www.docker.com) mit Docker Compose
- [Git](https://git-scm.com)
- [VS Code](https://code.visualstudio.com) mit den Extensions _Python_, _Ruff_,
  _ty_ und _AsciiDoc_ (empfohlen)
- [Bruno](https://www.usebruno.com) für API-Tests
- optional: Java und PlantUML für die Diagramme, OWASP Dependency Check CLI

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
Im laufenden Betrieb geht das auch mit `QUERY /dev/db_populate` (Admin-Token erforderlich).

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

## Backend starten

Für den Appserver müssen PostgreSQL, Keycloak und Mailpit laufen. Am einfachsten
startet man alle drei zusammen:

```shell
cd extras/compose/backend
docker compose up      # PostgreSQL, Keycloak und Mailpit
docker compose down    # herunterfahren, Daten bleiben erhalten
```

Mailpit zeigt die verschickten Mails unter <http://localhost:8025>.

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

## Docker und CI

Das `Dockerfile` folgt der Variante `Dockerfile.trixie` aus der Dozentenvorlage:
Python 3.15, Installation mit uv in einer Build-Stufe und Ausführung als Benutzer
`app` in einem separaten Laufzeit-Image.

Die lokale `.env` mit den eingerichteten Zugangsdaten wird auch hier benötigt.
Bereits separat gestartete Backend-Container vorher über ihre jeweilige
Compose-Konfiguration mit `down` ohne `-v` beenden, damit Namen und Ports frei sind.

```powershell
docker compose -p fitnessstudio -f extras/compose/mitglied/compose.yml up --build -d
docker compose -p fitnessstudio -f extras/compose/mitglied/compose.yml logs -f mitglied
docker compose -p fitnessstudio -f extras/compose/mitglied/compose.yml down
```

Die Anwendung ist unter <http://127.0.0.1:8000> erreichbar. Die Container-Konfiguration
steht in `extras/compose/mitglied/app.toml`. Wie in der Dozentenvorlage lädt
`db-populate = true` bei jedem Appstart die Mitgliedstabellen mit den Testdaten neu.
Für den Erhalt vorhandener Mitgliedsdaten nach der ersten Initialisierung auf
`false` setzen.

Der Workflow `.github/workflows/ci.yml` führt bei Push und Pull Request Ruff,
Typprüfung und die Unit-Tests mit Coverage aus und baut das Docker-Image.
Die Integrationstests benötigen separat laufende Dienste.

## Codeanalyse, Formatierung, Typprüfung und Tests

```shell
uv run ruff check src tests          # Codeanalyse
uv run ruff check --fix src tests    # Befunde automatisch beheben
uv run ruff format src tests         # Formatierung
uv run ty check                      # Typprüfung

uv run pytest tests/unit/mitglied    # Unit-Tests: ohne Server, DB und Keycloak
uv run pytest tests/integration      # Integrationstests: Backend und Appserver laufen
uv run pytest                        # alle Tests
```

Die **Unit-Tests** ersetzen Datenbank, Keycloak und Mailserver durch Mocks und
laufen auch in GitHub Actions. Die **Integrationstests** senden echte HTTP-Requests
an den laufenden Appserver (Default `http://127.0.0.1:8000`, änderbar mit der
Umgebungsvariablen `FITNESSSTUDIO_BASE_URL`) und lesen das Admin-Passwort aus `.env`.

`uv run pytest` erzeugt zusätzlich einen Testbericht (`report.html`) und
einen Bericht zur Testabdeckung (`htmlcov/index.html`).

Die Konfiguration aller Werkzeuge steht in `pyproject.toml`.

## Bruno

Die Bruno-Collection in `extras/bruno/mitglied` enthält Requests für REST und
GraphQL: Token holen, Suchen, Neu anlegen, Ändern mit `If-Match`, Löschen sowie
Fehlerfälle. In Bruno die Collection öffnen, die Umgebung `fitnessstudio` wählen und
dort die geheimen Variablen `password` und `clientSecret` eintragen.

## Lasttest mit Locust

```powershell
uv run locust -f tests/lasttest/locustfile.py --host http://127.0.0.1:8000
```

Danach <http://localhost:8089> öffnen. Details in
[tests/lasttest/README.md](tests/lasttest/README.md).

## Endpunkte

| Methode | Pfad | Rolle | Beschreibung |
| ------- | ---- | ----- | ------------ |
| GET | `/rest/{id}` | admin, mitglied | Ein Mitglied lesen (Mitglied: nur eigene Daten), `ETag` |
| GET | `/rest?nachname=&email=&page=&size=` | admin | Suche mit Pagination (`size` 1–100) |
| QUERY | `/rest/query` | admin | Suche mit Suchparametern im Request-Body |
| POST | `/rest` | – | Neues Mitglied anlegen, `201` mit `Location` |
| PUT | `/rest/{id}` | admin, mitglied | Ändern mit `If-Match`, `204` mit neuem `ETag` |
| DELETE | `/rest/{id}` | admin, mitglied | Löschen, `204` |
| QUERY | `/auth/token` | – | Login, liefert den JWT |
| POST | `/graphql` | siehe Doku | GraphQL: `mitglied`, `mitglieder`, `create`, `login` |
| QUERY | `/dev/db_populate` | admin | DB mit Testdaten neu laden (nur dev-Modus) |
| GET | `/` | – | `{"message": "Hello Fitnessstudio"}` |

OpenAPI-Dokumentation: <http://127.0.0.1:8000/docs>, GraphiQL:
<http://127.0.0.1:8000/graphql>.

## Projektstruktur

```text
fitnessstudio
├── pyproject.toml          Projektdaten, Abhängigkeiten, Konfiguration der Werkzeuge
├── uv.lock                 exakte Versionen aller Abhängigkeiten
├── Dockerfile              Docker-Image des Appservers
├── mkdocs.yml              Website mit API-Referenz
├── .env.example            Vorlage für die lokale .env mit den Passwörtern
├── .github/workflows       GitHub Actions: ruff, ty, Unit-Tests, Docker-Build
├── .agents, .claude        Library Skills zu FastAPI
├── docs                    AsciiDoc-Doku, PlantUML-Diagramme, mkdocs-Seiten
├── extras
│   ├── bruno               Requests für REST und GraphQL
│   ├── compose             backend, postgres, keycloak, mailpit, mitglied (Appserver)
│   ├── projektmanagement   Notizen
│   ├── dependency-check.py OWASP Dependency Check
│   └── suppression.xml     unterdrückte Befunde für Dependency Check
├── src
│   └── mitglied
│       ├── __init__.py     Einstiegspunkt main() für "uv run mitglied"
│       ├── fastapi_app.py  FastAPI-App, Middleware, Exception-Handler, lifespan
│       ├── problem_details.py  Fehler als application/problem+json
│       ├── config          app.toml, DB, Keycloak, Mail, dev-Modus
│       ├── entity          Entities für SQLAlchemy
│       ├── repository      DB-Zugriff, Suchparameter, Pagination
│       ├── service         Geschäftslogik, DTOs, Exceptions, Mailer
│       ├── router          REST-Endpunkte und Pydantic-Modelle
│       ├── graphql_api     GraphQL-Schema mit Strawberry
│       └── security        Token, Rollen, Login, Keycloak-Benutzer, Header
└── tests
    ├── unit/mitglied       Unit-Tests mit Mocks
    ├── integration         Tests gegen den laufenden Appserver
    └── lasttest            Lasttest mit Locust
```

## Datenmodell

- **Mitglied**: Vorname, Nachname, E-Mail (eindeutig ohne Groß-/Kleinschreibung),
  Geburtsdatum, Geschlecht, Interessen (JSON-Array), Version, Zeitstempel
- **Vertrag**: 1:0..1 zum Mitglied; Beginn, monatlicher Beitrag, Tarif
  (`BASIC`, `PREMIUM`, `STUDENT`), Getränkeflat
- **Zahlung**: 1:N zum Mitglied; Betrag, Zahlungsdatum

Das ER-Diagramm steht unter [Dokumentation](#dokumentation).

## Dokumentation

| Dokument | Inhalt |
| -------- | ------ |
| [docs/fitnessstudio.adoc](docs/fitnessstudio.adoc) | Projektdokumentation mit **AsciiDoctor** und **PlantUML**: Use Cases, Architektur, ER-Diagramm, Schnittstellen, Abläufe, Security |
| [docs/diagramme](docs/diagramme) | PlantUML-Quelltexte der Diagramme |
| [docs/img](docs/img) | gerenderte Diagramme als SVG |
| `mkdocs.yml` | Website mit API-Referenz aus den Docstrings |
| [extras/projektmanagement/notizen.md](extras/projektmanagement/notizen.md) | Notizen: Entscheidungen, Probleme, Checkliste |

Vorschau des AsciiDoc-Dokuments in VS Code: Extension _AsciiDoc_ installieren und in
den Einstellungen _Asciidoc › Extensions: Enable Kroki_ aktivieren. Diagramme nach
einer Änderung neu erzeugen (Java und `plantuml.jar` erforderlich):

```shell
cd docs/diagramme
java -jar plantuml.jar -tsvg -o ../img *.puml
```

Website mit mkdocs (Port 8000, deshalb vorher den Appserver beenden):

```shell
uv run mkdocs serve    # http://127.0.0.1:8000
uv run mkdocs build    # statische Website im Verzeichnis site
```

### ER-Diagramm

![ER-Diagramm](docs/img/er-diagramm.svg)

### Schichtenarchitektur

![Schichtenarchitektur](docs/img/schichtenarchitektur.svg)

## Weitere Werkzeuge

### OWASP Dependency Check

Prüft die Laufzeit-Abhängigkeiten auf bekannte Schwachstellen (CVEs). Voraussetzung
sind die Dependency Check CLI und ein kostenloser API-Key der NVD in `.env`
(siehe `.env.example`):

```powershell
uv run extras/dependency-check.py   # Bericht: dependency-check-report.html
```

Falsch-positive Befunde werden begründet in `extras/suppression.xml` eingetragen.

### Library Skills

Die Skills für KI-Agenten zu FastAPI liegen in `.agents/skills` und
`.claude/skills`. Sie stammen direkt aus dem installierten Paket `fastapi` und werden
nach einem Update von FastAPI aktualisiert:

```shell
uvx library-skills install --skill fastapi --copy --claude --yes
```

## Technologien

| Bereich                   | Technologie                               | Status |
| ------------------------- | ----------------------------------------- | ------ |
| Web-Framework             | FastAPI, uvicorn                          | ✅     |
| Projekt-Manager           | uv                                        | ✅     |
| Validierung               | Pydantic                                  | ✅     |
| OR-Mapping, Datenbank     | SQLAlchemy, psycopg, PostgreSQL           | ✅     |
| GraphQL                   | Strawberry                                | ✅     |
| Security (OIDC, OAuth 2)  | Keycloak, python-keycloak                 | ✅     |
| Mail                      | smtplib, Mailpit                          | ✅     |
| Protokollierung           | loguru                                    | ✅     |
| Codeanalyse, Formatierung | ruff                                      | ✅     |
| Typprüfung                | ty                                        | ✅     |
| Tests                     | pytest, pytest-cov, pytest-html           | ✅     |
| API-Tests                 | Bruno                                     | ✅     |
| Lasttests                 | Locust                                    | ✅     |
| Container                 | Docker, Docker Compose                    | ✅     |
| CI                        | GitHub Actions                            | ✅     |
| Dokumentation             | AsciiDoctor, PlantUML, mkdocs, mkdocstrings | ✅   |
| Sicherheitsanalyse        | OWASP Dependency Check                    | ✅     |
| KI-Agenten                | Library Skills                            | ✅     |

## Projektplan

Aufgaben und Fortschritt werden im
[GitHub Project](https://github.com/users/42esmmaa/projects/1) mit den Issues #1 bis
#11 verwaltet. Notizen (Entscheidungen, Probleme, bekannte Einschränkungen,
Checkliste für die Vorstellung) stehen in
[extras/projektmanagement/notizen.md](extras/projektmanagement/notizen.md).
