"""
Project-wide pytest configuration.

This file lives under `src/` because tests are located in `src/*/tests/`.
Keeping it at this level ensures it is applied to all test packages.
"""

from django.conf import settings


def pytest_configure() -> None:
    """
    Ensure test runs do not depend on external services.

    The project settings are configured for Postgres, but local/CI test runs
    should not require a running database server.
    """

    settings.DEBUG = False
    settings.DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
