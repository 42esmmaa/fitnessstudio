"""Exceptions in der Geschäftslogik."""

lazy from mitglied.repository.mitglied_suchparameter import MitgliedSuchparameter

__all__ = [
    "EmailExistsError",
    "ForbiddenError",
    "NotFoundError",
    "VersionOutdatedError",
]


class EmailExistsError(Exception):
    """Exception, falls die Emailadresse bereits existiert."""

    def __init__(self, email: str) -> None:
        """Initialisierung von EmailExistsError mit der Emailadresse.

        :param email: Bereits existierende Emailadresse
        """
        super().__init__(f"Existierende Email: {email}")
        self.email = email


class ForbiddenError(Exception):
    """Exception, falls es der Zugriff nicht erlaubt ist."""


class NotFoundError(Exception):
    """Exception, falls kein Mitglied gefunden wurde."""

    def __init__(
        self,
        mitglied_id: int | None = None,
        suchparameter: MitgliedSuchparameter | None = None,
    ) -> None:
        """Initialisierung von NotFoundError mit ID und Suchparameter.

        :param mitglied_id: Mitglied-ID, zu der nichts gefunden wurde
        :param suchparameter: Suchparameter, zu denen nichts gefunden wurde
        """
        super().__init__("Not Found")
        self.mitglied_id = mitglied_id
        self.suchparameter = suchparameter


class VersionOutdatedError(Exception):
    """Exception, falls die Versionsnummer beim Aktualisieren veraltet ist."""

    def __init__(self, version: int) -> None:
        """Initialisierung von VersionOutdatedError mit veralteter Versionsnummer.

        :param version: Veraltete Versionsnummer
        """
        super().__init__(f"Veraltete Version: {version}")
        self.version = version
