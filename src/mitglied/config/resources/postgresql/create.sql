-- Tabellen, Enum-Typen und Indexe fuer die DB "mitglied" im Schema "mitglied"
-- Aufruf beim Serverstart (dev-Modus) bzw. durch POST /dev/db_populate
--
-- TEXT statt VARCHAR(n): in PostgreSQL ohne Performance-Unterschied
-- https://www.postgresql.org/docs/current/datatype-character.html

-- Enum-Typen: SQLAlchemy speichert die NAMEN der Python-Enums, z.B. MAENNLICH statt M
-- https://www.postgresql.org/docs/current/datatype-enum.html
CREATE TYPE geschlecht AS ENUM ('MAENNLICH', 'WEIBLICH', 'DIVERS');
CREATE TYPE tarif AS ENUM ('BASIC', 'PREMIUM', 'STUDENT');

-- https://www.postgresql.org/docs/current/sql-createtable.html
CREATE TABLE IF NOT EXISTS mitglied (
                  -- IDs ab 1000 generieren, die Testdaten haben kleinere IDs
    id            INTEGER GENERATED ALWAYS AS IDENTITY(START WITH 1000) PRIMARY KEY,
                  -- Versionsnummer fuer optimistische Synchronisation
    version       INTEGER NOT NULL DEFAULT 0,
    vorname       TEXT NOT NULL,
    nachname      TEXT NOT NULL,
                  -- UNIQUE erzeugt implizit einen Index
    email         TEXT NOT NULL UNIQUE,
    geburtsdatum  DATE NOT NULL CHECK (geburtsdatum < current_date),
    geschlecht    geschlecht NOT NULL,
                  -- JSON-Array mit Strings, z.B. ["Yoga", "Krafttraining"]
                  -- https://www.postgresql.org/docs/current/datatype-json.html
    interessen    JSONB,
    erzeugt       TIMESTAMP NOT NULL,
    aktualisiert  TIMESTAMP NOT NULL
);

-- fuer die Suche nach dem Nachnamen; Default: B-Baum
CREATE INDEX IF NOT EXISTS mitglied_nachname_idx ON mitglied(nachname);

-- 1:1-Beziehung: UNIQUE bei mitglied_id, d.h. max. 1 Vertrag pro Mitglied
CREATE TABLE IF NOT EXISTS vertrag (
    id                  INTEGER GENERATED ALWAYS AS IDENTITY(START WITH 1000) PRIMARY KEY,
    beginn              DATE NOT NULL,
                        -- 6 Stellen, davon 2 Nachkommastellen
    monatlicher_beitrag NUMERIC(6,2) NOT NULL CHECK (monatlicher_beitrag >= 0),
    tarif               tarif NOT NULL,
    getraenkeflat       BOOLEAN NOT NULL DEFAULT FALSE,
    mitglied_id         INTEGER NOT NULL UNIQUE REFERENCES mitglied ON DELETE CASCADE
);

-- 1:N-Beziehung: beliebig viele Zahlungen pro Mitglied
CREATE TABLE IF NOT EXISTS zahlung (
    id            INTEGER GENERATED ALWAYS AS IDENTITY(START WITH 1000) PRIMARY KEY,
    betrag        NUMERIC(8,2) NOT NULL CHECK (betrag > 0),
    zahlungsdatum DATE NOT NULL,
    mitglied_id   INTEGER NOT NULL REFERENCES mitglied ON DELETE CASCADE
);

-- Fremdschluessel bekommen in PostgreSQL nicht automatisch einen Index
CREATE INDEX IF NOT EXISTS zahlung_mitglied_id_idx ON zahlung(mitglied_id);
