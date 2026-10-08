# Fitnessstudio

Appserver für die Mitgliederverwaltung eines Fitnessstudios, entwickelt mit
[FastAPI](https://fastapi.tiangolo.com) im Rahmen der Vorlesung
_Software Engineering_ an der Hochschule Karlsruhe (Aufgabe 1).

## Team

| Name            | E-Mail             |
| --------------- | ------------------ |
| Esma Ak         | akes1011@h-ka.de   |
| Eyübhan Yörümez | yoey1011@h-ka.de   |

## Inhalt

- [Projektstand](#projektstand)
- [Voraussetzungen](#voraussetzungen)
- [Installation und Start](#installation-und-start)
- [Endpunkte](#endpunkte)
- [Projektstruktur](#projektstruktur)
- [Datenmodell](#datenmodell)
- [Technologien](#technologien)
- [Projektplan](#projektplan)

## Projektstand

Der Server läuft und beantwortet einen ersten GET-Request mit „Hello World“.
Alle weiteren Funktionen sind geplant und im [Projektplan](#projektplan) erfasst.

## Voraussetzungen

- [Python](https://www.python.org) 3.15
- [uv](https://docs.astral.sh/uv) als Package- und Projekt-Manager
- [Git](https://git-scm.com)
- [VS Code](https://code.visualstudio.com) (empfohlen)

## Installation und Start

```shell
git clone https://github.com/42esmmaa/fitnessstudio.git
cd fitnessstudio

# virtuelle Umgebung .venv anlegen und Abhängigkeiten installieren
uv sync

# Server starten
uv run mitglied
```

Danach ist der Server unter <http://127.0.0.1:8000> erreichbar. Die
automatisch erzeugte API-Dokumentation von FastAPI gibt es unter
<http://127.0.0.1:8000/docs>.

## Endpunkte

| Methode | Pfad | Beschreibung                        |
| ------- | ---- | ----------------------------------- |
| GET     | `/`  | Liefert `{"message": "Hello Fitnessstudio"}` |

## Projektstruktur

```text
fitnessstudio
├── pyproject.toml          Projektdaten, Abhängigkeiten, Startskript
├── uv.lock                 exakte Versionen aller Abhängigkeiten
└── src
    └── mitglied
        ├── __init__.py     Einstiegspunkt main() für "uv run mitglied"
        ├── asgi_server.py  Start von uvicorn
        └── fastapi_app.py  FastAPI-App mit den Endpunkten
```

## Datenmodell

_(geplant)_

- **Mitglied**: Name, E-Mail, Geburtsdatum, Tarif
- **Adresse**: 1:1 zum Mitglied
- **Check-in**: Trainingsbesuche, 1:N zum Mitglied

Das ER-Diagramm wird ergänzt, sobald das Datenmodell feststeht.

## Technologien

| Bereich                     | Technologie            | Status   |
| --------------------------- | ---------------------- | -------- |
| Web-Framework               | FastAPI, uvicorn       | ✅       |
| Projekt-Manager             | uv                     | ✅       |
| Validierung                 | pydantic               | geplant  |
| OR-Mapping, Datenbank       | SQLAlchemy, PostgreSQL | geplant  |
| GraphQL                     | Strawberry             | geplant  |
| Security (OIDC, OAuth 2)    | Keycloak               | geplant  |
| Codeanalyse, Formatierung   | ruff                   | geplant  |
| Typprüfung                  | ty                     | geplant  |
| Tests                       | pytest                 | geplant  |
| Lasttests                   | Locust                 | geplant  |
| Container                   | Docker, Docker Compose | geplant  |
| CI                          | GitHub Actions         | geplant  |
| API-Tests                   | Bruno                  | geplant  |

## Projektplan

Aufgaben und Fortschritt werden im GitHub Project zu diesem Repository
verwaltet (Reiter _Projects_).
