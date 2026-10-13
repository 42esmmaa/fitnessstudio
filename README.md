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
- Alle weiteren Funktionen sind im [Projektplan](#projektplan) erfasst.

## Voraussetzungen

- [Python](https://www.python.org) 3.15
- [uv](https://docs.astral.sh/uv) als Package- und Projekt-Manager
- [Git](https://git-scm.com)
- [VS Code](https://code.visualstudio.com) mit den Extensions _Python_, _Ruff_
  und _ty_ (empfohlen)

## Installation und Start

```shell
git clone https://github.com/42esmmaa/fitnessstudio.git
cd fitnessstudio

# virtuelle Umgebung .venv anlegen und alle Abhängigkeiten installieren
uv sync

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

## Projektstruktur

```text
fitnessstudio
├── pyproject.toml          Projektdaten, Abhängigkeiten, Konfiguration der Werkzeuge
├── uv.lock                 exakte Versionen aller Abhängigkeiten
├── src
│   └── mitglied
│       ├── __init__.py     Einstiegspunkt main() für "uv run mitglied"
│       ├── __main__.py     Aufruf mit "python -m mitglied"
│       ├── __about__.py    Versionsnummer
│       ├── asgi_server.py  Start von uvicorn
│       └── fastapi_app.py  FastAPI-App mit den Endpunkten
└── tests
    └── hello_test.py       erster Test mit dem TestClient von FastAPI
```

## Datenmodell

_(geplant)_

- **Mitglied**: Name, E-Mail, Geburtsdatum, Tarif
- **Adresse**: 1:1 zum Mitglied
- **Check-in**: Trainingsbesuche, 1:N zum Mitglied

Das ER-Diagramm wird ergänzt, sobald das Datenmodell feststeht.

## Technologien

| Bereich                   | Technologie                        | Status  |
| ------------------------- | ---------------------------------- | ------- |
| Web-Framework             | FastAPI, uvicorn                   | ✅      |
| Projekt-Manager           | uv                                 | ✅      |
| Codeanalyse, Formatierung | ruff                               | ✅      |
| Typprüfung                | ty                                 | ✅      |
| Tests                     | pytest, pytest-cov, pytest-html    | ✅      |
| Validierung               | pydantic                           | geplant |
| OR-Mapping, Datenbank     | SQLAlchemy, PostgreSQL             | geplant |
| GraphQL                   | Strawberry                         | geplant |
| Security (OIDC, OAuth 2)  | Keycloak                           | geplant |
| Lasttests                 | Locust                             | geplant |
| Container                 | Docker, Docker Compose             | geplant |
| CI                        | GitHub Actions                     | geplant |
| API-Tests                 | Bruno                              | geplant |

## Projektplan

Aufgaben und Fortschritt werden im
[GitHub Project](https://github.com/users/42esmmaa/projects/1) zu diesem
Repository verwaltet.
