-- Alles aus create.sql wieder entfernen, in umgekehrter Reihenfolge der Abhaengigkeiten

DROP INDEX IF EXISTS
    zahlung_mitglied_id_idx,
    mitglied_email_idx,
    mitglied_nachname_idx;

-- zuerst die Tabellen mit Fremdschluesseln, zuletzt "mitglied"
DROP TABLE IF EXISTS
    zahlung,
    vertrag,
    mitglied;

DROP TYPE IF EXISTS
    geschlecht,
    tarif;
