"""
Common pytest fixtures for tests in this Django project.
"""

from django.conf import settings


def pytest_configure() -> None:
    """
    Disable Django debug mode for tests.

    This keeps test logs quiet and makes behavior deterministic.
    """

    settings.DEBUG = False

    # Use a fast in-memory database for tests by default.
    #
    # The project settings are configured for Postgres, but local/CI test runs
    # should not require an external database service.
    settings.DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
