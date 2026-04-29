# sloths-inventory

## Overview

Django-based inventory application.

The primary user-facing interface is a simple "My items" page that shows the
equipment currently assigned to the logged-in user and allows viewing the item
history.

## User interface

- **Root page**: `GET /` shows **My items** (requires authentication).
- **Item history**: `GET /items/<id>/` shows the item's operations history (only
  for items currently assigned to the logged-in user).
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
