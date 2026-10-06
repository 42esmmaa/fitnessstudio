"""Start der Anwendung mit uvicorn."""

import uvicorn


def run() -> None:
    """Server auf Port 8000 starten."""
    uvicorn.run("mitglied:app", host="127.0.0.1", port=8000)