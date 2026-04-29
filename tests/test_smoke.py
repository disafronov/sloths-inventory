def test_django_settings_import() -> None:
    """Smoke test: Django settings module can be imported."""

    # pytest-django configures Django based on DJANGO_SETTINGS_MODULE.
    from django.conf import settings

    assert settings is not None

