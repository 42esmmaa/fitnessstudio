"""FastAPI-Anwendung."""

from typing import Final

from fastapi import FastAPI

app: Final = FastAPI(title="Fitnessstudio")


@app.get("/")
def hello() -> dict[str, str]:
    """Erster GET-Request: Hello World als dict."""
    return {"message": "Hello Fitnessstudio"}
