from __future__ import annotations

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
            "(run with DJANGO_SETTINGS_MODULE=sloths_inventory.settings)"
        )
