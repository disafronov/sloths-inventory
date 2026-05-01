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
  for items currently assigned to the logged-in user, items the user had in the past,
  or items that have an active incoming transfer offer for the logged-in user).
- **Admin UI**: `GET /admin/`
- **Health**: `GET /health/liveness/`, `GET /health/readiness/`

### Account linking

The user-facing inventory pages (`/`, `/previous/`, `/items/<id>/`) are scoped by
the `Responsible` profile linked to the authenticated `User`
(`catalogs.Responsible.user`).

`Responsible` is a domain entity and can exist without any Django `User`. Linking
to a `User` is optional and is only required for the user-facing pages. If the
current `User` is not linked, the UI will show a message and no items.

To link an account, open the Django admin, edit the desired `Responsible` record
and set its `user` field to the corresponding Django `User`.

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
docker compose up -d
```

Notes:

- `docker compose` in this repository is intended to run **PostgreSQL only** for
  local development.
- Run Django locally with `make run` and point it to the Postgres instance via
  env vars (see `env.example`).
- The Docker image itself starts the application with **Gunicorn** (see
  `Dockerfile`) and serves static files via **WhiteNoise**.
- If you run the image directly (without Docker Compose), you must run migrations
  yourself.
- If you want to run the Docker image against the local Postgres started via
  `docker compose up -d`, use `env.docker` (it points `DATABASE_HOST` to
  `host.docker.internal`). On Linux, `make docker-run` includes the required host
  mapping (`--add-host=host.docker.internal:host-gateway`).

## Domain rules

- **Append-only operations**: an item's state is tracked via `Operation` records.
  Older operations cannot be edited; only the latest operation for an item may be
  corrected.
- **Correction window**: editing the latest operation is only allowed within a
  limited time window after it was created. The window is configurable via
  `INVENTORY_OPERATION_EDIT_WINDOW_MINUTES` (default: 10 minutes).
- **Item history visibility**: item history is only accessible to the current
  owner, to the receiver of an active incoming transfer offer, and to former owners.
  Former owners can only see the history up to the last time the item was assigned
  to them, plus one subsequent handoff operation.
  This is a privacy/security invariant: it provides enough context for a handoff
  dispute ("when and to whom it was transferred") without exposing the item's
  subsequent history to former owners.
- **Transfer offer expiry**: offers created from the user UI get an `expires_at`
  timestamp when `INVENTORY_PENDING_TRANSFER_EXPIRATION_HOURS` is positive
  (default: one week). After that moment the offer is no longer active unless
  changed in the admin.

## Configuration

The application is configured via environment variables (loaded using
`django-environ`).

See `env.example` for a complete list of supported variables.

- **Django**
  - `DEBUG`: enable debug mode (default: `0`)
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
  - `INVENTORY_PENDING_TRANSFER_EXPIRATION_HOURS` (default: `168` — one week;
    offers created from the user UI get `expires_at` at creation. Set to `0` to
    disable automatic expiry unless set manually in the admin)

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

Note: use `make` targets for checks (`make all`, `make test`, `make lint`). They
set a tooling-only `SECRET_KEY` for `pytest` and `mypy` so local runs do not
depend on developer environment variables.

### PostgreSQL-only tests

The default test configuration runs Django with in-memory SQLite
(`sloths_inventory.settings_pytest`) for speed and to avoid requiring a running
Postgres instance.

Some tests validate PostgreSQL-specific behavior (e.g. row-level locking). Such
tests are marked with `@pytest.mark.postgres` and are automatically skipped
unless the active database backend is PostgreSQL.

Note: `src/conftest.py` is test infrastructure (not application code) and is
excluded from coverage.

Rule of thumb: add `@pytest.mark.postgres` when a test relies on PostgreSQL
semantics or query planning, for example:

- row-level locks / blocking behavior (`select_for_update()`)
- transaction isolation / concurrency edge cases
- PostgreSQL-specific SQL or index/ordering behavior

To run tests on PostgreSQL locally, enable PostgreSQL for pytest:

```bash
PYTEST_POSTGRES_USE=1 \
DATABASE_HOST=127.0.0.1 DATABASE_PORT=5432 \
DATABASE_NAME=database DATABASE_USER=user DATABASE_PASSWORD=password \
PYTHONPATH=src SECRET_KEY=unsafe-secret-key-for-tooling \
uv run python -m pytest -v
```

Formatting is intentionally not part of `make all` (so checks do not mutate the
working tree). To auto-format code, use:

```bash
make format
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
  skipped on SQLite). CI runs PostgreSQL-only tests in a dedicated workflow
  (**Tests Postgres**).
- **Testing entrypoint**: `manage.py test` is intentionally disabled; use `make test`
  or `make all` instead.
