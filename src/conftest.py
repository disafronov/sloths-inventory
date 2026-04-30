from __future__ import annotations

import os

import pytest
from django.db import connections


def pytest_runtest_setup(item: pytest.Item) -> None:
    """
    Enforce database backend requirements for marked tests.

    The default test run uses SQLite (see `sloths_inventory.settings_pytest`) for
    speed and to keep local development infrastructure-free. Some tests must
    validate PostgreSQL-specific semantics (e.g. row-level locks), so they are
    marked with `@pytest.mark.postgres` and are skipped unless the active DB
    vendor is PostgreSQL.
    """

    if "postgres" not in item.keywords:
        return

    if connections["default"].vendor != "postgresql":
        pytest.skip(
            "requires PostgreSQL "
            "(run with PYTEST_POSTGRES_USE=1 and PostgreSQL DATABASE_* env vars)"
        )


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    """
    Optionally restrict collection to PostgreSQL-only tests via env vars.

    The repository uses SQLite as the default pytest database backend for speed.
    CI runs the PostgreSQL-only subset in a dedicated workflow. To keep the CI
    command simple and environment-driven, we support selecting only the tests
    marked with `@pytest.mark.postgres` via env vars (without passing `-m`).
    """

    use_postgres = os.environ.get("PYTEST_POSTGRES_USE") in {"1", "true", "True"}
    postgres_only = os.environ.get("PYTEST_POSTGRES_ONLY") in {"1", "true", "True"}

    if not (use_postgres and postgres_only):
        return

    selected: list[pytest.Item] = []
    deselected: list[pytest.Item] = []
    for item in items:
        if "postgres" in item.keywords:
            selected.append(item)
        else:
            deselected.append(item)

    if deselected:
        config.hook.pytest_deselected(items=deselected)
        items[:] = selected
