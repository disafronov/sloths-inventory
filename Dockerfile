FROM ubuntu:latest

# Change the working directory to the `app` directory
WORKDIR /app

# Install dependencies
RUN --mount=from=ghcr.io/astral-sh/uv,source=/uv,target=/bin/uv \
    --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --link-mode=copy

# Copy the project into the image
COPY ./sloths_inventory/ /app/sloths_inventory/

# Sync the project
RUN --mount=from=ghcr.io/astral-sh/uv,source=/uv,target=/bin/uv \
    --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --link-mode=copy

ENV PATH="/app/.venv/bin:$PATH"

ENTRYPOINT [ "python3", "sloths_inventory/manage.py", "runserver", "0.0.0.0:8000" ]
EXPOSE 8000
