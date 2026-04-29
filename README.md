# sloths-inventory

## Overview

Django-based inventory application.

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

Run using Docker Compose:

```bash
docker compose up --build
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
