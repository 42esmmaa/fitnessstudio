"""Konfiguration für Mailserver."""

from dataclasses import dataclass
from email.headerregistry import Address
from typing import Final

from loguru import logger

from mitglied.config.config import app_config

__all__ = ["mail_config", "receiver", "sender"]


_mail_toml: Final = app_config.get("mail", {})


@dataclass(frozen=True, eq=False, slots=True)
class MailConfig:
    """Konfiguration für Mailserver."""

    enabled: bool = bool(_mail_toml.get("enabled", True))
    """True, falls der Mailserver aktiviert ist."""

    host: str = _mail_toml.get("host", "mail")
    """Rechnername des Mailservers."""

    port: int = _mail_toml.get("port", 25)
    """Port des Mailservers."""

    timeout: float = _mail_toml.get("timeout", 1.0)
    """Timeout für den Mailserver in Sekunden."""


mail_config: Final = MailConfig()
logger.debug("mail_config={}", mail_config)
sender: Final[Address] = Address(
    display_name="Fitnessstudio Server",
    username="fitnessstudio.server",
    domain="acme.com",
)
"""Absender der E-Mails."""

receiver: Final[Address] = Address(
    display_name="Buchhaltung", username="buchhaltung", domain="acme.com"
)
"""Empfänger der E-Mails."""
