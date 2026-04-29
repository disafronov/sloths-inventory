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
