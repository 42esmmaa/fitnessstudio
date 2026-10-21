#!/bin/bash
# DB-User, Datenbank und Schema "keycloak" fuer den Keycloak-Container anlegen
# wird beim 1. Start des Containers (leeres Volume) ausgefuehrt,
# alphabetisch zwischen create-db.sh und create-schema.sql
#
# Das Passwort kommt aus der Umgebungsvariablen KC_DB_PASSWORD (aus .env).
# Keycloak liest dieselbe Variable, damit beide Seiten das gleiche Passwort haben.

# ggf. Windows-Zeilenende entfernen, falls .env mit CRLF gespeichert wurde
passwort="${KC_DB_PASSWORD%$'\r'}"
if [ -z "$passwort" ]; then
    echo "FEHLER: KC_DB_PASSWORD ist nicht gesetzt (siehe .env.example)" >&2
    exit 1
fi

psql -v ON_ERROR_STOP=1 \
     --username "${POSTGRES_USER:-postgres}" \
     --dbname postgres \
     -v passwort="$passwort" <<'EOSQL'
CREATE USER keycloak PASSWORD :'passwort';
CREATE DATABASE keycloak OWNER keycloak;

-- Schema "keycloak" in der DB "keycloak" (wie KC_DB_SCHEMA in keycloak/compose.yml)
\connect keycloak
CREATE SCHEMA IF NOT EXISTS AUTHORIZATION keycloak;
ALTER ROLE keycloak SET search_path = 'keycloak';
EOSQL
