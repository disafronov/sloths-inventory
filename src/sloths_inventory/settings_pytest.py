"""
Pytest settings module.

Pytest (via pytest-django) should be self-contained and must not require a running
Postgres instance in CI.
"""

import secrets

from .settings import *  # noqa: F401,F403

# Keep test output deterministic and quiet.
DEBUG = False  # noqa: F405
SECRET_KEY = secrets.token_urlsafe(32)  # noqa: F405

# Force in-memory SQLite for pytest runs.
DATABASES = {  # noqa: F405
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Keep settings compatible with Django system checks when env vars are not set.
ALLOWED_HOSTS = [h for h in ALLOWED_HOSTS if h]  # noqa: F405
CSRF_TRUSTED_ORIGINS = [o for o in CSRF_TRUSTED_ORIGINS if o]  # noqa: F405
