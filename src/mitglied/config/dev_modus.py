"""Konfiguration für den Entwicklungsmodus."""

from typing import Final

from mitglied.config.config import app_config

__all__ = ["dev_db_populate"]

_dev_toml: Final = app_config.get("dev", {})

dev_db_populate: Final[bool] = bool(_dev_toml.get("db-populate", False))
"""True, falls die DB beim Serverstart neu geladen werden soll."""
