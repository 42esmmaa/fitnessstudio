"""Konfiguration aus der TOML-Datei einlesen und Logging einrichten."""

from importlib.resources import files
from pathlib import Path
from sys import stderr
from tomllib import load
from typing import Any, Final

from dotenv import load_dotenv
from loguru import logger

__all__ = ["app_config", "resources_path"]


# Passwoerter aus der lokalen Datei .env im Projektverzeichnis als Umgebungsvariable
# bereitstellen; bereits gesetzte Umgebungsvariablen werden NICHT ueberschrieben.
# .env steht in .gitignore, die Vorlage ist .env.example.
load_dotenv(Path.cwd() / ".env")

resources_path: Final = "mitglied.config.resources"
"""Package mit den Ressourcen, z.B. app.toml und SQL-Skripte."""

_config_file: Final = files(resources_path) / "app.toml"

with Path(str(_config_file)).open(mode="rb") as reader:
    app_config: Final[dict[str, Any]] = load(reader)
    """Inhalt von app.toml als dict."""

_logger_toml: Final = app_config.get("logger", {})
_logger_debug: Final[bool] = bool(_logger_toml.get("debug-level", False))

LOG_FILE: Final = Path("log") / "app.log"
# Default von loguru: Level DEBUG auf stderr
if _logger_debug:
    logger.add(LOG_FILE, rotation="1 MB")
else:
    logger.remove()
    logger.add(stderr, level="INFO")
    logger.add(LOG_FILE, rotation="1 MB", level="INFO")

logger.info("Logging ist konfiguriert")
logger.debug("config: app_config={}", app_config)
