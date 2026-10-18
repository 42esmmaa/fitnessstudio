"""DB im dev-Modus mit drop.sql, create.sql und CSV-Dateien neu laden."""

from importlib.resources import files
from pathlib import Path
from typing import Final

from loguru import logger
from sqlalchemy import Connection, create_engine, text

from mitglied.config.config import resources_path
from mitglied.config.db import db_connect_args, db_log_statements, db_url_admin
from mitglied.config.dev_modus import dev_db_populate
from mitglied.repository import engine

__all__ = ["DbPopulateService", "db_populate", "get_db_populate_service"]

_SQL_PATH: Final = files(resources_path) / "postgresql"

# Reihenfolge wegen der Fremdschlüssel: zuerst "mitglied"
_TABELLEN: Final = ("mitglied", "vertrag", "zahlung")

# Verzeichnis IM DB-Container, siehe extras/compose/postgres/compose.yml
_CSV_PATH: Final = "/init/mitglied/csv"


class DbPopulateService:
    """Neuladen der DB im dev-Modus."""

    def __init__(self) -> None:
        """Engine für den Superuser erstellen, weil nur er COPY ... FROM darf."""
        self.engine_admin: Final = create_engine(
            db_url_admin,
            connect_args=db_connect_args,
            echo=db_log_statements,
        )

    def populate(self) -> None:
        """Tabellen löschen, neu anlegen und mit den CSV-Dateien füllen."""
        logger.warning(">>> Die DB wird neu geladen: {} <<<", engine.url)
        # Als DB-User "mitglied", damit ihm die Tabellen gehören
        with engine.begin() as connection:
            self._execute_script("drop.sql", connection)
            self._execute_script("create.sql", connection)
        self._load_csv_files()
        logger.warning(">>> Die DB wurde neu geladen <<<")

    def _execute_script(self, dateiname: str, connection: Connection) -> None:
        skript: Final = Path(str(_SQL_PATH / dateiname)).read_text()
        for statement in self.split_statements(skript):
            connection.execute(text(statement))

    @staticmethod
    def split_statements(skript: str) -> list[str]:
        """SQL-Skript in einzelne Anweisungen zerlegen.

        Alles ab `--` bis zum Zeilenende ist ein Kommentar und wird entfernt.
        Die Anweisungen werden am `;` getrennt.

        :param skript: Inhalt eines SQL-Skripts
        :return: Liste der SQL-Anweisungen ohne `;`
        :rtype: list[str]
        """
        ohne_kommentare: Final = "\n".join(
            zeile.split("--", maxsplit=1)[0] for zeile in skript.splitlines()
        )
        return [
            statement.strip()
            for statement in ohne_kommentare.split(";")
            if statement.strip()
        ]

    def _load_csv_files(self) -> None:
        # COPY liest die Dateien auf dem DB-Server, nicht auf dem Rechner des Appservers
        with self.engine_admin.begin() as connection:
            connection.execute(text("SET search_path TO mitglied"))
            for tabelle in _TABELLEN:
                logger.debug("tabelle={}", tabelle)
                # Tabellenname aus der festen Liste oben, keine Benutzereingabe
                copy_cmd = (
                    f"COPY {tabelle} FROM '{_CSV_PATH}/{tabelle}.csv' "
                    "(FORMAT csv, DELIMITER ';', HEADER true)"
                )
                connection.execute(text(copy_cmd))
        self.engine_admin.dispose()


def get_db_populate_service() -> DbPopulateService:
    """Factory-Funktion für DbPopulateService, z.B. für Depends()."""
    return DbPopulateService()


def db_populate() -> None:
    """DB mit Testdaten neu laden, falls in app.toml `db-populate = true` ist."""
    if dev_db_populate:
        get_db_populate_service().populate()
