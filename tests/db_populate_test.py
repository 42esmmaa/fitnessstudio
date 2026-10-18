"""Unit-Tests für das Zerlegen der SQL-Skripte beim Neuladen der DB."""

from importlib.resources import files

from mitglied.config.dev.db_populate import DbPopulateService

# create.sql: 2 Enum-Typen, 3 Tabellen, 3 Indexe
ANZAHL_CREATE = 8
# drop.sql: je 1 Anweisung fuer Indexe, Tabellen und Enum-Typen
ANZAHL_DROP = 3


def test_split_statements_ohne_kommentare() -> None:
    skript = """
    -- Kommentarzeile
    CREATE TABLE a (
        id INTEGER, -- Kommentar am Zeilenende
        name TEXT
    );

    DROP TABLE b;
    """
    create_table, drop_table = DbPopulateService.split_statements(skript)
    assert create_table.startswith("CREATE TABLE a (")
    assert "--" not in create_table
    assert drop_table == "DROP TABLE b"


def test_split_statements_create_und_drop() -> None:
    sql_path = files("mitglied.config.resources") / "postgresql"
    create = DbPopulateService.split_statements((sql_path / "create.sql").read_text())
    drop = DbPopulateService.split_statements((sql_path / "drop.sql").read_text())
    assert len(create) == ANZAHL_CREATE
    assert len(drop) == ANZAHL_DROP
