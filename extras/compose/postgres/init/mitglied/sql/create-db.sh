#!/bin/bash
# DB-User und Datenbank "mitglied" anlegen
# wird beim 1. Start des Containers (leeres Volume) ausgefuehrt, vor create-schema.sql
#
# Das Passwort kommt aus der Umgebungsvariablen MITGLIED_DB_PASSWORD (aus .env),
# damit es in keiner Datei im Repository steht.

# ggf. Windows-Zeilenende entfernen, falls .env mit CRLF gespeichert wurde
passwort="${MITGLIED_DB_PASSWORD%$'\r'}"
if [ -z "$passwort" ]; then
    echo "FEHLER: MITGLIED_DB_PASSWORD ist nicht gesetzt (siehe .env.example)" >&2
    exit 1
fi

# psql-Variable :'passwort' wird als String-Literal eingesetzt, d.h. sicher gequotet
psql -v ON_ERROR_STOP=1 \
     --username "${POSTGRES_USER:-postgres}" \
     --dbname postgres \
     -v passwort="$passwort" <<'EOSQL'
-- https://www.postgresql.org/docs/current/sql-createrole.html
CREATE USER mitglied PASSWORD :'passwort';

-- https://www.postgresql.org/docs/current/sql-createdatabase.html
CREATE DATABASE mitglied OWNER mitglied;
EOSQL
