# Keycloak als Authorization Server

Keycloak läuft als Docker-Container und speichert seine Daten in einer
**eigenen Datenbank** `keycloak` (DB-User `keycloak`, Schema `keycloak`) im
PostgreSQL-Container aus `extras/compose/postgres`. Aufbau nach dem Beispiel
von Jürgen Zimmermann (`extras/compose/keycloak` im Projekt _fastapi_), aber
DB, Realm, Client, Rollen und Testbenutzer werden automatisch angelegt.

## Inhalt

- [Voraussetzungen](#voraussetzungen)
- [Starten](#starten)
- [Realm, Client, Rollen und Benutzer](#realm-client-rollen-und-benutzer)
- [Client Secret](#client-secret)
- [Access Token testen](#access-token-testen)
- [Neu anlegen](#neu-anlegen)

## Voraussetzungen

In der lokalen `.env` im Projektverzeichnis (siehe `.env.example`) stehen:

- `KC_DB_PASSWORD`: Passwort des DB-Users `keycloak`
- `KC_BOOTSTRAP_ADMIN_PASSWORD`: Passwort des temporären Administrators `tmp`

Die DB `keycloak` legt das Skript
`extras/compose/postgres/init/mitglied/sql/create-keycloak-db.sh` an. Es läuft
nur beim **ersten** Start von PostgreSQL mit leerem Volume. Gibt es das Volume
schon, muss es einmal neu angelegt werden (die Tabellen und Testdaten von
`mitglied` lädt der Appserver beim Start ohnehin neu):

```shell
cd extras/compose/postgres
docker compose down -v
```

## Starten

`compose.yml` bindet `../postgres/compose.yml` ein, d.h. PostgreSQL wird
mitgestartet. Ein schon laufender PostgreSQL-Container aus
`extras/compose/postgres` muss vorher heruntergefahren werden, weil beide den
Containernamen `postgres` haben.

```shell
cd extras/compose/keycloak
docker compose up      # PostgreSQL und Keycloak starten
docker compose down    # beide herunterfahren, Daten bleiben erhalten
```

Der erste Start dauert etwa 1 Minute. Danach:

| URL                                  | Zweck                       |
| ------------------------------------ | --------------------------- |
| `https://localhost:8843`             | Admin-Konsole (HTTPS)       |
| `http://localhost:8880`              | Admin-Konsole (HTTP)        |
| `http://localhost:9990/health/ready` | Health-Check                |

Admin-Konsole: Benutzername `tmp`, Passwort `KC_BOOTSTRAP_ADMIN_PASSWORD` aus
`.env`. Das Zertifikat in `tls/` ist selbst-signiert, der Browser warnt deshalb.

OpenID-Konfiguration des Realms:
`https://localhost:8843/realms/fitnessstudio/.well-known/openid-configuration`

## Realm, Client, Rollen und Benutzer

Beim Start wird `import/fitnessstudio-realm.json` importiert (nur wenn der Realm
noch nicht existiert):

- Realm `fitnessstudio`
- Client `fitnessstudio-client` mit _Client authentication_, _Standard flow_,
  _Direct access grants_ und _Service account roles_
- Client-Rollen `admin` und `mitglied`, passend zu `Role.ADMIN` und
  `Role.MITGLIED` in `src/mitglied/security/role.py` (im Token stehen sie unter
  `resource_access.fitnessstudio-client.roles`)
- Access Token 30 Minuten, SSO-Session 1 Stunde

| Benutzer | Passwort | Rollen                                    | wie in `mitglied.csv`     |
| -------- | -------- | ----------------------------------------- | ------------------------- |
| `admin`  | `p`      | `admin`, Benutzerverwaltung (realm-admin) | `admin@fitnessstudio.de`  |
| `alice`  | `p`      | `mitglied`                                | `alice@fitnessstudio.de`  |
| `bob`    | `p`      | `mitglied`                                | `bob@fitnessstudio.de`    |

Die Passwörter sind nur für die lokale Entwicklung gedacht.

## Client Secret

Das Client Secret erzeugt Keycloak beim Import selbst. Man findet es in der
Admin-Konsole:

- Realm `fitnessstudio` auswählen
- Menüpunkt `Clients` → `fitnessstudio-client` → Tab `Credentials`
- Wert bei `Client Secret` kopieren

Es wird später für den Appserver (`.env`) und für Bruno gebraucht und gehört
**nicht** ins Repository.

## Access Token testen

```powershell
# Windows PowerShell; $secret = Client Secret von oben
curl.exe -k -X POST https://localhost:8843/realms/fitnessstudio/protocol/openid-connect/token `
  -d grant_type=password -d client_id=fitnessstudio-client -d client_secret=$secret `
  -d username=admin -d password=p
```

Den `access_token` aus der Antwort kann man auf <https://jwt.io> dekodieren und
dort die Rollen prüfen.

## Neu anlegen

Nach Änderungen an `fitnessstudio-realm.json` wird der Realm nicht automatisch
aktualisiert. Entweder in der Admin-Konsole den Realm löschen und Keycloak neu
starten, oder alles neu anlegen:

```shell
cd extras/compose/keycloak
docker compose down -v
docker compose up
```

Achtung: `down -v` löscht hier auch das Volume von PostgreSQL (wegen `include`),
also auch die DB `mitglied`. Deren Tabellen und Testdaten lädt der Appserver
beim nächsten Start wieder, ein neues Client Secret muss man aber erneut kopieren.
