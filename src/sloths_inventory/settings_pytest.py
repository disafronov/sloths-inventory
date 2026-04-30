"""
Pytest settings module.

Pytest (via pytest-django) should be self-contained and must not require a running
Postgres instance in CI.
"""

from .settings import *  # noqa: F401,F403

# Static files in tests should not depend on `collectstatic`.
#
# The production settings use WhiteNoise's manifest-based storage, which requires a
# generated manifest. In pytest runs we render templates that include `{% static %}`
# and we want those tests to be hermetic, so we switch to the non-manifest storage.
STORAGES = dict(STORAGES)  # noqa: F405
STORAGES["staticfiles"] = {  # noqa: F405
    "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
}

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
