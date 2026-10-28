"""Funktionen für E-Mails."""

from email.message import EmailMessage
from email.utils import make_msgid
from html import escape
from smtplib import SMTP, SMTPException
from socket import gaierror
from typing import Final
from uuid import uuid4

from loguru import logger

from mitglied.config import mail_config, receiver, sender
lazy from mitglied.service.mitglied_dto import MitgliedDTO

__all__ = ["send_mail"]


def send_mail(mitglied_dto: MitgliedDTO) -> None:
    """Funktion, um eine E-Mail zu senden.

    :param mitglied_dto: Mitgliedsdaten
    """
    logger.debug("{}", mitglied_dto)
    if not mail_config.enabled:
        logger.warning("send_mail: Der Mailserver ist deaktiviert")
        return
    msg: Final = EmailMessage()
    msg["From"] = sender
    msg["To"] = (receiver,)
    msg["Subject"] = f"Neues Mitglied: ID={mitglied_dto.id}"
    msg["Message-ID"] = make_msgid(idstring=str(uuid4()))

    msg.set_content(f"Neues Mitglied: {mitglied_dto.nachname}")

    # Benutzereingaben im HTML immer maskieren
    msg.add_alternative(
        f"Neues Mitglied: <b>{escape(mitglied_dto.nachname)}</b>",
        subtype="html",
    )

    try:
        with SMTP(
            host=mail_config.host, port=mail_config.port, timeout=mail_config.timeout
        ) as smtp:
            # ggf. TLS verwenden und einloggen
            # smtp.starttls()
            # smtp.login("my_username", "my_password")
            logger.debug("msg={}", msg)
            smtp.send_message(msg)
    except ConnectionRefusedError:
        # ConnectionRefusedError -> ConnectionError -> OSError
        logger.warning("ConnectionRefusedError")
    except TimeoutError:
        logger.warning("TimeoutError beim Senden der E-Mail")
    except gaierror:
        # gai = getaddrinfo()  # NOSONAR
        logger.warning("socket.gaierror: Laeuft der Mailserver im virtuellen Netzwerk?")
    except SMTPException as err:
        # alle SMTP-Fehler, z.B. SMTPServerDisconnected oder SMTPRecipientsRefused:
        # der Mailversand im Hintergrund darf den Server nicht stoeren
        logger.warning("{}: {}", type(err).__name__, err)
