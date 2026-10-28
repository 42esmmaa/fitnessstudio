# Notizen zu Aufgabe 1 (Appserver mit FastAPI)

Projektplan: [GitHub Project](https://github.com/users/42esmmaa/projects/1) und
Issues #1 bis #11.

## Aufteilung im Team

| Bereich | Hauptsächlich |
| ------- | ------------- |
| Projekt-Setup, uv, ruff, ty, pytest, README | Esma |
| PostgreSQL, SQL-Skripte, Testdaten, Neuladen der DB | Esma |
| Keycloak-Container, Realm, Rollen | Esma |
| Entities, Repository, Pagination | Eyübhan (Repository-Feinschliff: Esma) |
| Services, DTOs, Pydantic-Modelle, REST-Router | Eyübhan |
| TokenService, UserService, Mail, GraphQL, Bruno | Eyübhan |
| Docker-Image, GitHub Actions | Eyübhan |
| Code-Review, Eigentümerprüfung, Validierung, Doku, Lasttest | Esma |

Grundlage ist die Git-Historie (`git shortlog -sn`). Bei der Vorstellung muss
trotzdem **jede/r das komplette Projekt** erklären können.

## Entscheidungen

- **Schichten** Router → Service → Repository → Entity wie in der Vorlage; zwischen
  Service und Router werden DTOs statt Entities weitergegeben.
- **Paketname `mitglied`**, Projektname `fitnessstudio`: deshalb
  `module-name = "mitglied"` in `pyproject.toml`.
- **IDs ab 1000** (`IDENTITY START WITH 1000`), damit die Testdaten mit kleinen IDs
  nicht mit neuen Datensätzen kollidieren.
- **Email eindeutig ohne Groß-/Kleinschreibung**: Index auf `lower(email)` in der DB
  und Normalisierung mit `@validates` in der Entity.
- **Suche per `QUERY`** zusätzlich zu `GET`: Suchkriterien im Request-Body statt in der
  URL (landen dann nicht in Logs und Browser-Historie).
- **Optimistische Synchronisation** mit `ETag`/`If-Match` und `version_id_col`
  statt Sperren.
- **Mitglied darf nur eigene Daten** lesen, ändern und löschen. Vergleich über die
  Email im Token. Für fremde *und* nicht vorhandene IDs: `403`, damit man nicht
  herausfinden kann, welche IDs es gibt.
- **Neuanlage mit Keycloak**: erst DB prüfen, dann Keycloak-User anlegen, bei einem
  DB-Fehler den Keycloak-User wieder löschen (Kompensation, keine gemeinsame
  Transaktion möglich).
- **Mail als BackgroundTask**: wird erst nach dem Response gesendet, der Client wartet
  nicht auf den Mailserver.
- **Passwörter nur in `.env`**, Vorlage `.env.example` im Repository.
- **Zeilenenden LF** für alle Dateien (`.gitattributes`), sonst z.B. `\r` im Passwort
  unter Windows.

## Probleme und Erkenntnisse

- `size=0` bei der Suche lieferte alle Datensätze ohne `LIMIT` → jetzt `size >= 1`.
- Versionsprüfung mit `>` ließ eine *zu hohe* Version durch → jetzt `!=`.
- Nachname-Regex aus der Vorlage erlaubte keine Doppelnamen
  (`Müller-Lüdenscheidt`) → `+` nach dem Bindestrich ergänzt.
- Keycloak-User blieb bei einem DB-Fehler übrig → Kompensation ergänzt.
- `async def` mit synchronem DB-Zugriff blockiert die Event-Loop → `def` bzw.
  `run_in_threadpool`.
- Python 3.15: `lazy from ... import ...` (PEP 810) vermeidet zirkuläre Imports
  zwischen Entities und Services.

## Bekannte Einschränkungen

- Neue Mitglieder erhalten in Keycloak das feste Passwort `p` (wie in der Vorlage).
- `POST /rest` ist ohne Login erreichbar (Registrierung).
- Beim Löschen eines Mitglieds bleibt der Benutzer in Keycloak bestehen.
- Ändert ein Mitglied seine eigene Email, passt sie nicht mehr zur Email im Token
  und der Zugriff auf die eigenen Daten geht verloren.
- Zertifikatsprüfung zu Keycloak ist abgeschaltet (`verify=False`, selbst-signiert).

## Einsatz von KI

Für Code-Review, einzelne Korrekturen, Tests, Lasttest und Dokumentation wurde ein
KI-Assistent (Claude) verwendet. Alle Änderungen wurden von uns gelesen,
nachvollzogen und mit ruff, ty und pytest geprüft (Folie 15: Code, den man nicht
versteht, gilt als Täuschungsversuch).

## Checkliste für die Vorstellung

- [ ] Link zum Repository abgegeben
- [ ] Beide Notebooks: `uv sync`, `.env` angelegt, Container gestartet
      (PostgreSQL, Keycloak, Mailpit), Client Secret aus Keycloak in `.env`
- [ ] `uv run mitglied` startet, `/docs` und `/graphql` erreichbar
- [ ] `uv run pytest` grün (Unit- und Integrationstests)
- [ ] Bruno: Token holen, Suchen, Anlegen, Ändern mit `If-Match`, Löschen
- [ ] Locust einmal laufen lassen
- [ ] Docker-Image bauen und mit Compose starten
- [ ] GitHub Actions grün
- [ ] Jede/r kann jede Schicht und jeden Commit erklären
