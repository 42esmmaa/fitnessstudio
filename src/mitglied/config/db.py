"""DB-URLs für SQLAlchemy aus der Konfiguration erstellen."""

from os import getenv
from typing import Final

from loguru import logger
from sqlalchemy.engine import URL

from mitglied.config.config import app_config

__all__ = ["db_connect_args", "db_log_statements", "db_url", "db_url_admin"]

_db_toml: Final = app_config.get("db", {})

# psycopg 3 als DB-Treiber https://www.psycopg.org/psycopg3
_DRIVERNAME: Final = "postgresql+psycopg"
_dbname: Final[str] = _db_toml.get("name", "mitglied")
_host: Final[str] = _db_toml.get("host", "postgres")
_port: Final[int] = _db_toml.get("port", 5432)
_username: Final[str] = _db_toml.get("username", "mitglied")
# Passwoerter NICHT aus app.toml, sondern aus Umgebungsvariablen bzw. der Datei .env
_password: Final = getenv("MITGLIED_DB_PASSWORD")
_password_admin: Final = getenv("POSTGRES_PASSWORD")
if _password is None or _password_admin is None:
    logger.warning(
        "MITGLIED_DB_PASSWORD oder POSTGRES_PASSWORD fehlt: .env anlegen, "
        "siehe .env.example"
    )

db_log_statements: Final[bool] = bool(_db_toml.get("log-statements", False))
"""True, falls SQLAlchemy die SQL-Anweisungen protokollieren soll."""

db_url: Final = URL.create(
    drivername=_DRIVERNAME,
    username=_username,
    password=_password,
    host=_host,
    port=_port,
    database=_dbname,
)
"""DB-URL für den DB-User der Anwendung."""
logger.debug("db: db_url={}", db_url)

db_url_admin: Final = URL.create(
    drivername=_DRIVERNAME,
    username="postgres",
    password=_password_admin,
    host=_host,
    port=_port,
    database=_dbname,
)
"""DB-URL für den Superuser `postgres`, z.B. für COPY beim Neuladen der DB."""

# TLS ist noch nicht eingerichtet: "prefer" nutzt TLS nur, falls der Server es anbietet.
# Später mit Zertifikat: "verify-full" und "sslrootcert".
db_connect_args: Final[dict[str, str]] = {
    "sslmode": _db_toml.get("sslmode", "prefer"),
}
"""Zusätzliche Verbindungsparameter für psycopg."""
