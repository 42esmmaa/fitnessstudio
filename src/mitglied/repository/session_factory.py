"""Engine und Factory für Sessions von SQLAlchemy konfigurieren."""

from typing import Final

from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from mitglied.config import db_connect_args, db_log_statements, db_url

__all__ = ["Session", "engine"]

# Die Engine verwaltet einen Pool von DB-Verbindungen. Eine Verbindung wird erst
# beim ersten DB-Zugriff aufgebaut, nicht schon beim Import dieses Moduls.
# Default-Isolationslevel von PostgreSQL: READ COMMITTED
engine: Final = create_engine(
    db_url,
    connect_args=db_connect_args,
    pool_size=10,
    echo=db_log_statements,
)
"""Engine für SQLAlchemy, um DB-Verbindungen und Sessions zu erstellen."""
logger.info("Engine fuer SQLAlchemy erzeugt")

# autoflush=False: SQL-Anweisungen erst beim Commit bzw. explizitem flush() senden
Session: Final = sessionmaker(bind=engine, autoflush=False)
"""Factory für Sessions, um SQL-Anweisungen in Transaktionen abzusetzen."""
