"""Filter für die Mitgliedersuche."""

from dataclasses import dataclass

__all__ = ["MitgliedSuchparameter"]


@dataclass(frozen=True, slots=True, kw_only=True)
class MitgliedSuchparameter:
    """Suchparameter für die Mitgliedersuche."""

    email: str | None = None
    """Exakte Emailadresse als Suchparameter."""

    nachname: str | None = None
    """Teil des Nachnamens als Suchparameter."""

    def is_empty(self) -> bool:
        """Prüft, ob kein Suchparameter gesetzt ist."""
        return self.email is None and self.nachname is None
