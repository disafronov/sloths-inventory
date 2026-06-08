"""
Pytest settings module.

Pytest (via pytest-django) should be self-contained and must not require a running
Postgres instance in CI.

Note: run tests via `make test` / `make all` so the tooling-only `SECRET_KEY` is
provided via environment variables.
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

# Tests do not serve static files through WhiteNoise, and the production
# STATIC_ROOT may not exist before collectstatic runs.
MIDDLEWARE = [  # noqa: F405
    middleware
    for middleware in MIDDLEWARE  # noqa: F405
    if middleware != "whitenoise.middleware.WhiteNoiseMiddleware"
]

# Keep settings compatible with Django system checks when env vars are not set.
ALLOWED_HOSTS = [h for h in ALLOWED_HOSTS if h]  # noqa: F405
CSRF_TRUSTED_ORIGINS = [o for o in CSRF_TRUSTED_ORIGINS if o]  # noqa: F405

EMAIL_SEND_ASYNC = False
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Keep secure flags off during tests to avoid HTTPS redirects and
# Secure-only cookies in the test client.
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

INVENTORY_CORRECTION_WINDOW_MINUTES = 10
