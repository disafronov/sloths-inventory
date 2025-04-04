FROM ubuntu:latest AS base

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
COPY ./sloths_inventory/ /app/sloths_inventory/

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

#! <MVP ONLY!
ENTRYPOINT [ "python3", "sloths_inventory/manage.py", "runserver", "0.0.0.0:8000", "--noreload" ]
#! MVP ONLY!>

EXPOSE 8000
