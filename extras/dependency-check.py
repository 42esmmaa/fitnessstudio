"""OWASP Dependency Check für die Python-Abhängigkeiten aufrufen.

Voraussetzungen:

- Dependency Check CLI installiert, z.B. nach `C:/Zimmermann/dependency-check`
  (https://github.com/dependency-check/DependencyCheck/releases)
- Java ab Version 11
- in `.env`: `NVD_API_KEY=...` (kostenlos: https://nvd.nist.gov/developers/request-an-api-key)
  und optional `DEPENDENCY_CHECK_HOME=...`, falls die CLI woanders installiert ist

Aufruf im Projektverzeichnis:

```powershell
uv run extras/dependency-check.py
```

Der Bericht steht danach in `dependency-check-report.html`. Der erste Aufruf dauert
lange, weil die Schwachstellen-Datenbank der NVD heruntergeladen wird.
"""

import subprocess  # ruff: ignore[suspicious-subprocess-import]
import sys
from os import environ
from pathlib import Path
from shutil import which
from typing import Final

from dotenv import load_dotenv

load_dotenv()

PROJEKT: Final = "fitnessstudio"
BUILD_PATH: Final = Path("build")
REQUIREMENTS: Final = BUILD_PATH / "requirements.txt"
SUPPRESSION: Final = Path("extras") / "suppression.xml"


def _cli() -> Path:
    """Pfad zum Start-Skript der Dependency Check CLI ermitteln."""
    windows: Final = sys.platform == "win32"
    default_home: Final = (
        Path("C:/Zimmermann/dependency-check") if windows else Path("dependency-check")
    )
    home: Final = Path(environ.get("DEPENDENCY_CHECK_HOME", str(default_home)))
    return home / "bin" / ("dependency-check.bat" if windows else "dependency-check.sh")


def _requirements_exportieren() -> None:
    """Exakte Versionen aus uv.lock als requirements.txt exportieren.

    Dependency Check kann uv.lock nicht lesen, wohl aber requirements.txt.
    """
    uv: Final = which("uv")
    if uv is None:
        sys.exit("uv wurde nicht gefunden")
    BUILD_PATH.mkdir(exist_ok=True)
    subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true]
        [
            uv,
            "export",
            "--format",
            "requirements-txt",
            "--no-hashes",
            # nur die Laufzeit-Abhaengigkeiten, d.h. ohne dev, doc und lint
            "--no-default-groups",
            "--output-file",
            str(REQUIREMENTS),
        ],
        check=True,
    )


def main() -> None:
    """requirements.txt erzeugen und Dependency Check aufrufen."""
    cli: Final = _cli()
    if not cli.exists():
        sys.exit(f"Dependency Check nicht gefunden: {cli} (DEPENDENCY_CHECK_HOME?)")
    nvd_api_key: Final = environ.get("NVD_API_KEY")
    if not nvd_api_key:
        sys.exit("NVD_API_KEY fehlt in .env")

    _requirements_exportieren()

    args: Final = [
        str(cli),
        "--project",
        PROJEKT,
        "--scan",
        str(REQUIREMENTS),
        "--suppression",
        str(SUPPRESSION),
        "--out",
        ".",
        "--format",
        "HTML",
        "--nvdApiKey",
        nvd_api_key,
        # Analyse von requirements.txt ist bei Dependency Check "experimental"
        "--enableExperimental",
        # nur Python analysieren: Java-, JavaScript-, .NET-Analyzer usw. abschalten
        "--disableAssembly",
        "--disableCentral",
        "--disableJar",
        "--disableNodeAudit",
        "--disableNodeJS",
        "--disableOssIndex",
        "--disableRetireJS",
        "--disableYarnAudit",
        "--disablePnpmAudit",
    ]
    # Der API-Key wird absichtlich nicht ausgegeben
    print(f"Dependency Check fuer {REQUIREMENTS} wird gestartet ...")
    ergebnis: Final = subprocess.run(args, check=False)  # ruff: ignore[subprocess-without-shell-equals-true]
    sys.exit(ergebnis.returncode)


if __name__ == "__main__":
    main()
