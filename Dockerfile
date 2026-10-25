# syntax=docker/dockerfile:1.27.0
# check=error=true

# ARG: "build-time" Variable
# ENV: "build-time" und "runtime" Variable
ARG PYTHON_VERSION_UV=3.15-rc
ARG PYTHON_VERSION=3.15.0rc2
ARG UV_VERSION=0.12.20

# ------------------------------------------------------------------------------
# S t a g e   b u i l d e r
# ------------------------------------------------------------------------------
FROM ghcr.io/astral-sh/uv:${UV_VERSION}-python${PYTHON_VERSION_UV}-trixie-slim AS builder

# Install the project into `/opt/app`
WORKDIR /opt/app

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Enable bytecode compilation
# Copy from the cache instead of linking since it's a mounted volume
# Kein Python-Download, falls eine "managed" Python-Version verwendet wird,
# sondern in beiden Images denselben Python-Interpreter verwenden
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0 \
    UV_PROJECT_ENVIRONMENT=/opt/app/.venv \
    PATH="/root/.cargo/bin:$PATH"

RUN <<EOF
set -eux
# Die "Package Index"-Dateien neu synchronisieren
apt-get update --no-show-upgraded
# Die neuesten Versionen der bereits installierten Packages installieren
apt-get upgrade --yes --no-show-upgraded
apt-get install --no-install-recommends --yes --show-progress curl=8.14.1-2+deb13u7 gcc=4:14.2.0-1 libc6-dev=2.41-12+deb13u4
curl --proto '=https' --tlsv1.3 --silent --show-error --fail https://sh.rustup.rs | sh -s -- --default-toolchain stable --profile minimal --no-modify-path -y
EOF

# Install the project's dependencies using the lockfile and settings (siehe "[tool.uv]" in pyproject.toml)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-default-groups --no-editable

# Then, add the rest of the project source code and install it
# Installing separately from its dependencies allows optimal layer caching
COPY README.md pyproject.toml ./
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    uv sync --frozen --no-default-groups --no-editable

# ------------------------------------------------------------------------------
# S t a g e   f i n a l
# ------------------------------------------------------------------------------
FROM python:${PYTHON_VERSION}-slim-trixie AS final

ARG APP_UID=10000
ARG APP_GID=10000

# Anzeige bei "docker inspect ..."
LABEL org.opencontainers.image.title="mitglied" \
    org.opencontainers.image.description="Appserver mitglied mit Basis-Image Slim Trixie" \
    org.opencontainers.image.version="2026.10.1-trixie" \
    org.opencontainers.image.authors="akes1011@h-ka.de, yoey1011@h-ka.de"

RUN <<EOF
set -eux
# Die "Package Index"-Dateien neu synchronisieren
apt-get update
# Die neuesten Versionen der bereits installierten Packages installieren
apt-get upgrade --yes
apt-get autoremove --yes
apt-get clean --yes
rm -rf /var/lib/apt/lists/*
rm -rf /tmp/*
EOF

# "working directory" fuer die Docker-Kommandos RUN, ENTRYPOINT, CMD, COPY und ADD
WORKDIR /opt/app

RUN <<EOF
set -eux
groupadd --gid ${APP_GID} app
useradd --uid ${APP_UID} --gid ${APP_GID} --shell /bin/bash --no-create-home app
# User "app" als Owner fuer das working directory
chown -R ${APP_UID}:${APP_GID} /opt/app
EOF

# User "app" statt User "root"
USER ${APP_UID}:${APP_GID}

COPY --from=builder --chown=${APP_UID}:${APP_GID} /opt/app ./

# Place executables in the environment at the front of the path
ENV PATH="/opt/app/.venv/bin:$PATH"

EXPOSE 8000

STOPSIGNAL SIGINT

ENTRYPOINT ["python", "-m", "mitglied"]
