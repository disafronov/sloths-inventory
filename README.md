# sloths-inventory

## Overview

Django-based inventory application.

The primary user-facing interface is a simple "My items" page that shows the
equipment currently assigned to the logged-in user and allows viewing the item
history.

## User interface

- **Root page**: `GET /` shows **My items** (requires authentication).
- **Previously my items**: `GET /previous/` shows items that used to be assigned to
  the logged-in user (requires authentication).
- **Item history**: `GET /items/<id>/` shows the item's operations history (only
  for items currently assigned to the logged-in user, or items the user had in the past).
- **Admin UI**: `GET /admin/`
- **Health**: `GET /health/liveness/`, `GET /health/readiness/`

## Requirements

- `uv` package manager
- Python version: see `.python-version`

## Installation

```bash
make install
```

## Running

Run locally:

```bash
make run
```

Then open:

- `http://localhost:8000/` (will redirect to login if not authenticated)
- `http://localhost:8000/admin/`
- `http://localhost:8000/health/`

Run using Docker Compose:

```bash
docker compose up --build
```

Note: `docker compose` runs `manage.py migrate` on startup (see `compose.yml`
entrypoint config). The Docker image itself starts Django with `runserver` only
(see `Dockerfile`), so if you run the image directly you must run migrations
yourself.

## Domain rules

- **Append-only operations**: an item's state is tracked via `Operation` records.
  Older operations cannot be edited; only the latest operation for an item may be
  corrected.
- **Correction window**: editing the latest operation is only allowed within a
  limited time window after it was created. The window is configurable via
  `INVENTORY_OPERATION_EDIT_WINDOW_MINUTES` (default: 10 minutes).
- **Item history visibility**: item history is only accessible to the current
  owner and former owners. Former owners can only see the history up to the last
  time the item was assigned to them, plus one subsequent handoff operation.

## Configuration

The application is configured via environment variables (loaded using
`django-environ`).

- **Django**
  - `DEBUG`: enable debug mode (default: `1`)
  - `SECRET_KEY`: required when `DEBUG=0`
  - `ALLOWED_HOSTS`: comma-separated list
  - `CSRF_TRUSTED_ORIGINS`: comma-separated list
- **Database (PostgreSQL)**
  - `DATABASE_HOST` (default: `127.0.0.1`)
  - `DATABASE_PORT` (default: `5432`)
  - `DATABASE_NAME` (default: `database`)
  - `DATABASE_USER` (default: `user`)
  - `DATABASE_PASSWORD` (default: `password`)
- **Logging**
  - `LOG_LEVEL` (default: `DEBUG` when `DEBUG=1`, else `INFO`)
- **Inventory**
  - `INVENTORY_OPERATION_EDIT_WINDOW_MINUTES` (default: `10`)

## Localization

Translations are stored in `src/*/locale/*/LC_MESSAGES/django.po` and are
compiled into `.mo` files.

To compile translations locally:

```bash
PYTHONPATH=src uv run python src/manage.py compilemessages
```

## Run checks

```bash
make all
```

Run tests:

```bash
make test
```

Run tests with coverage:

```bash
make test-coverage
```

## Notes

- **Coverage 100%**: we exclude **typing-only** lines (e.g. `@overload`, `if TYPE_CHECKING:`, `...`) via coverage config in `pyproject.toml`.
- **Concurrency tests**: `inventory/tests/test_concurrency.py` validates
  row-level locking semantics and is intended to run on PostgreSQL (it is
  skipped on SQLite). CI runs these tests against Postgres in a dedicated job.
- **Testing entrypoint**: `manage.py test` is intentionally disabled; use `make test`
  or `make all` instead.
