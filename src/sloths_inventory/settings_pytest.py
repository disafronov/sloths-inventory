"""
Pytest settings module.

Pytest (via pytest-django) should be self-contained and must not require a running
Postgres instance in CI.

Note: run tests via `make test` / `make all` so the tooling-only `SECRET_KEY` is
provided via environment variables.
"""

from .settings import *  # noqa: F401,F403

# Opt-in PostgreSQL for marked tests.
#
# The default for pytest runs is in-memory SQLite for speed and hermetic local
# development. PostgreSQL-only tests (marked with `@pytest.mark.postgres`) can be
# enabled by setting `PYTEST_POSTGRES_USE=1` and providing standard DATABASE_*
# env vars (same as production settings).
PYTEST_POSTGRES_USE = env.bool("PYTEST_POSTGRES_USE", default=False)  # noqa: F405

# Static files in tests should not depend on `collectstatic`.
#
# The production settings use WhiteNoise's manifest-based storage, which requires a
# generated manifest. In pytest runs we render templates that include `{% static %}`
# and we want those tests to be hermetic, so we switch to the non-manifest storage.
STORAGES = dict(STORAGES)  # noqa: F405
STORAGES["staticfiles"] = {  # noqa: F405
    "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
}

# Default to in-memory SQLite for pytest runs (override via `PYTEST_POSTGRES_USE`).
if PYTEST_POSTGRES_USE:
    DATABASES = {  # noqa: F405
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("DATABASE_NAME", default="database"),  # noqa: F405
            "USER": env("DATABASE_USER", default="user"),  # noqa: F405
            "PASSWORD": env("DATABASE_PASSWORD", default="password"),  # noqa: F405
            "HOST": env("DATABASE_HOST", default="127.0.0.1"),  # noqa: F405
            "PORT": env("DATABASE_PORT", default="5432"),  # noqa: F405
        }
    }
else:
    DATABASES = {  # noqa: F405
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }

# Keep settings compatible with Django system checks when env vars are not set.
ALLOWED_HOSTS = [h for h in ALLOWED_HOSTS if h]  # noqa: F405
CSRF_TRUSTED_ORIGINS = [o for o in CSRF_TRUSTED_ORIGINS if o]  # noqa: F405
