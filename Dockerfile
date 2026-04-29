FROM ghcr.io/astral-sh/uv:0.11.8 AS uv

FROM ubuntu:noble-20260410 AS base

# ENVs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    TZ=Etc/UTC

# Base dependencies
RUN apt-get update && \
    apt-get install -y \
        tzdata && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

USER ubuntu:ubuntu
WORKDIR /home/ubuntu/app

# Create venv (uses .python-version from the build context).
RUN --mount=from=uv,source=/uv,target=/bin/uv \
    --mount=type=cache,target=/home/ubuntu/.cache/uv,uid=1000,gid=1000 \
    --mount=type=bind,source=.python-version,target=.python-version \
    uv venv

ENV PATH="/home/ubuntu/app/.venv/bin:$PATH"

##########################

FROM base AS builder

# Install dependencies first (without installing the project itself).
RUN --mount=from=uv,source=/uv,target=/bin/uv \
    --mount=type=cache,target=/home/ubuntu/.cache/uv,uid=1000,gid=1000 \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=.python-version,target=.python-version \
    uv sync --frozen --no-install-project --link-mode=copy --no-editable --no-group dev

# Copy the project into the image
COPY ./src/ /home/ubuntu/app/src/

# Sync the project now that sources exist.
RUN --mount=from=uv,source=/uv,target=/bin/uv \
    --mount=type=cache,target=/home/ubuntu/.cache/uv,uid=1000,gid=1000 \
    --mount=type=bind,source=README.md,target=README.md \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --link-mode=copy --no-editable --no-dev

##########################

FROM base AS runtime

# Copy venv and app files from builder stage.
COPY --from=builder /home/ubuntu/app/.venv/ /home/ubuntu/app/.venv/
COPY ./ /home/ubuntu/app/

WORKDIR /home/ubuntu/app/src

#! <MVP ONLY!
ENTRYPOINT [ "python3", "manage.py", "runserver", "0.0.0.0:8000", "--noreload" ]
#! MVP ONLY!>

EXPOSE 8000
