"""Mailversand ohne echten SMTP-Server prüfen."""

from datetime import date
from smtplib import SMTPRecipientsRefused, SMTPServerDisconnected
from socket import gaierror
from unittest.mock import patch

import pytest

from mitglied.config import receiver, sender
from mitglied.config.mail import MailConfig
from mitglied.entity import Geschlecht
from mitglied.service import MitgliedDTO, send_mail


@pytest.fixture
def mitglied_dto() -> MitgliedDTO:
    """Mitgliedsdaten für die Benachrichtigung bereitstellen."""
    return MitgliedDTO(
        id=1000,
        version=1,
        vorname="Alex",
        nachname="Muster",
        email="alex@example.org",
        geburtsdatum=date(2000, 1, 1),
        geschlecht=Geschlecht.DIVERS,
        vertrag=None,
        interessen=None,
    )


@pytest.fixture
def smtp():
    """Aktivierten Versand mit simuliertem SMTP bereitstellen."""
    with (
        patch(
            "mitglied.service.mailer.mail_config",
            MailConfig(enabled=True, host="localhost", port=1025, timeout=1.0),
        ),
        patch("mitglied.service.mailer.SMTP") as mock,
    ):
        yield mock


def test_send_mail_nachrichtenaufbau(mitglied_dto, smtp) -> None:
    send_mail(mitglied_dto)
    smtp.assert_called_once_with(host="localhost", port=1025, timeout=1.0)
    verbindung = smtp.return_value.__enter__.return_value
    verbindung.send_message.assert_called_once()
    nachricht = verbindung.send_message.call_args.args[0]
    assert str(nachricht["From"]) == str(sender)
    assert str(nachricht["To"]) == str(receiver)
    assert nachricht["Subject"] == "Neues Mitglied: ID=1000"
    assert nachricht["Message-ID"] is not None
    assert (
        "Neues Mitglied: Muster"
        in nachricht.get_body(preferencelist=("plain",)).get_content()
    )
    assert "<b>Muster</b>" in nachricht.get_body(preferencelist=("html",)).get_content()
    smtp.return_value.__exit__.assert_called_once_with(None, None, None)


def test_send_mail_deaktiviert(mitglied_dto, smtp) -> None:
    with patch("mitglied.service.mailer.mail_config", MailConfig(enabled=False)):
        send_mail(mitglied_dto)
    smtp.assert_not_called()


@pytest.mark.parametrize(
    "fehler", [ConnectionRefusedError, SMTPServerDisconnected, TimeoutError, gaierror]
)
def test_send_mail_verbindungsfehler(mitglied_dto, smtp, fehler) -> None:
    smtp.side_effect = fehler("Testfehler")
    send_mail(mitglied_dto)
    smtp.assert_called_once()


def test_send_mail_maskiert_html(mitglied_dto, smtp) -> None:
    mitglied_dto.nachname = "<script>{x}</script>"
    send_mail(mitglied_dto)
    nachricht = smtp.return_value.__enter__.return_value.send_message.call_args.args[0]
    html = nachricht.get_body(preferencelist=("html",)).get_content()
    assert "<script>" not in html
    assert "&lt;script&gt;{x}&lt;/script&gt;" in html


def test_send_mail_sonstiger_smtp_fehler(mitglied_dto, smtp) -> None:
    smtp.return_value.__enter__.return_value.send_message.side_effect = (
        SMTPRecipientsRefused({})
    )
    send_mail(mitglied_dto)
    smtp.return_value.__exit__.assert_called_once()


def test_send_mail_verbindung_bricht_beim_senden_ab(mitglied_dto, smtp) -> None:
    smtp.return_value.__enter__.return_value.send_message.side_effect = (
        SMTPServerDisconnected("Testfehler")
    )
    send_mail(mitglied_dto)
    smtp.return_value.__exit__.assert_called_once()
