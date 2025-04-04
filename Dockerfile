FROM ubuntu:noble-20250127 AS base

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

# Change the working directory to the `app` directory
WORKDIR /app

##########################

FROM base AS builder

# Install dependencies
RUN --mount=from=ghcr.io/astral-sh/uv,source=/uv,target=/bin/uv \
    --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --link-mode=copy --no-editable --no-dev

# Copy the project into the image
COPY ./src/ /app/src/

# Sync the project
RUN --mount=from=ghcr.io/astral-sh/uv,source=/uv,target=/bin/uv \
    --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --link-mode=copy --no-editable --no-dev

##########################

FROM base AS runtime

# Use python from UV
COPY --from=builder /root/.local/share/uv/python/ /root/.local/share/uv/python/

# Copy app directory from builder
COPY --from=builder --chown=app:app /app/ /app/

ENV PATH="/app/.venv/bin:$PATH"

# Change the working directory to the `django project` directory
WORKDIR /app/src

#! <MVP ONLY!
ENTRYPOINT [ "python3", "manage.py", "runserver", "0.0.0.0:8000", "--noreload" ]
#! MVP ONLY!>

EXPOSE 8000
