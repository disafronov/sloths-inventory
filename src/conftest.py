from __future__ import annotations

import os
from typing import Any

import pytest
from django.db import connections

from catalogs.models import Location, Status
from devices.models import Device


def _env_truthy(name: str) -> bool:
    return os.environ.get(name) in {"1", "true", "True"}


def pytest_configure(config: pytest.Config) -> None:
    """
    Validate pytest configuration derived from env vars.

    We allow controlling the PostgreSQL test subset via env vars to keep CI
    commands simple. Some combinations are invalid and should fail fast.
    """

    use_postgres = _env_truthy("PYTEST_POSTGRES_USE")
    postgres_only = _env_truthy("PYTEST_POSTGRES_ONLY")

    if postgres_only and not use_postgres:
        raise pytest.UsageError(
            "Invalid pytest configuration: PYTEST_POSTGRES_ONLY=1 requires "
            "PYTEST_POSTGRES_USE=1 (and PostgreSQL DATABASE_* env vars)."
        )


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

    use_postgres = _env_truthy("PYTEST_POSTGRES_USE")
    postgres_only = _env_truthy("PYTEST_POSTGRES_ONLY")

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


@pytest.fixture
def inventory_test_device(db: Any) -> Device:
    """
    Standard ``Device`` row with category/type/manufacturer/model for tests.

    Reduces duplicated catalog graph setup across inventory and related suites.
    """

    from devices.attributes import Category, Manufacturer, Model, Type

    category = Category.objects.create(name="Laptops")
    device_type = Type.objects.create(name="Laptop")
    manufacturer = Manufacturer.objects.create(name="ACME")
    device_model = Model.objects.create(name="Model X")
    return Device.objects.create(
        category=category,
        type=device_type,
        manufacturer=manufacturer,
        model=device_model,
    )


@pytest.fixture
def inventory_test_status_location(db: Any) -> dict[str, Location | Status]:
    """Typical ``Status`` and ``Location`` rows for inventory operation tests."""

    return {
        "status": Status.objects.create(name="In stock"),
        "location": Location.objects.create(name="Moscow"),
    }
