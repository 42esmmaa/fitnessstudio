-- Schema "mitglied" in der DB "mitglied" anlegen
-- wird nach create-db.sql ausgefuehrt (alphabetische Reihenfolge)

-- psql-Kommando: Verbindung zur DB "mitglied" statt "postgres"
\connect mitglied

-- "user-private schema" statt des Default-Schemas "public"
-- https://www.postgresql.org/docs/current/ddl-schemas.html
CREATE SCHEMA IF NOT EXISTS AUTHORIZATION mitglied;

-- Tabellen ohne Schema-Praefix werden im Schema "mitglied" gesucht und angelegt
ALTER ROLE mitglied SET search_path = 'mitglied';
