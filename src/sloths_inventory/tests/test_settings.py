import importlib.util
from types import ModuleType

import pytest
from django.core.exceptions import ImproperlyConfigured

import sloths_inventory.settings


def _load_module_from_path(module_name: str, path: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_settings_requires_secret_key_when_debug_false(monkeypatch) -> None:
    monkeypatch.setenv("DEBUG", "0")
    monkeypatch.delenv("SECRET_KEY", raising=False)

    with pytest.raises(
        ImproperlyConfigured, match="Set the SECRET_KEY environment variable"
    ):
        _load_module_from_path(
            "sloths_inventory._settings_no_secret_key_test",
            sloths_inventory.settings.__file__,
        )


def test_settings_accepts_secret_key_when_debug_false(monkeypatch) -> None:
    monkeypatch.setenv("DEBUG", "0")
    monkeypatch.setenv("SECRET_KEY", "not-a-secret-value")

    module = _load_module_from_path(
        "sloths_inventory._settings_with_secret_key_test",
        sloths_inventory.settings.__file__,
    )
    assert module.SECRET_KEY == "not-a-secret-value"


def test_settings_defaults_secret_key_when_debug_true(tmp_path, monkeypatch) -> None:
    """
    Ensure DEBUG mode has a deterministic SECRET_KEY default.

    `settings.py` reads `.env` at import time; we change CWD to a temporary empty
    directory to avoid picking up any repository-local `.env` during tests.
    """

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DEBUG", "1")
    monkeypatch.delenv("SECRET_KEY", raising=False)

    module = _load_module_from_path(
        "sloths_inventory._settings_debug_default_secret_key_test",
        sloths_inventory.settings.__file__,
    )
    assert module.SECRET_KEY == "unsafe-secret-key"


def test_settings_time_zone_defaults_when_env_is_unset(tmp_path, monkeypatch) -> None:
    """
    Ensure TIME_ZONE is configurable and has a deterministic default.

    `settings.py` reads `.env` at import time; we change CWD to a temporary empty
    directory to avoid picking up any repository-local `.env` during tests.
    """

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("TIME_ZONE", raising=False)

    module = _load_module_from_path(
        "sloths_inventory._settings_time_zone_default_test",
        sloths_inventory.settings.__file__,
    )
    assert module.TIME_ZONE == "UTC"


def test_settings_time_zone_can_be_overridden_via_env(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TIME_ZONE", "UTC")

    module = _load_module_from_path(
        "sloths_inventory._settings_time_zone_env_override_test",
        sloths_inventory.settings.__file__,
    )
    assert module.TIME_ZONE == "UTC"


def test_settings_inventory_correction_window_minutes_defaults_when_env_unset(
    tmp_path, monkeypatch
) -> None:
    """
    ``INVENTORY_CORRECTION_WINDOW_MINUTES`` defaults to 0 when the env var is absent.

    Uses an isolated CWD so ``environ.Env.read_env()`` does not pick up a repo-local
    ``.env`` while importing ``settings.py``.
    """

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("INVENTORY_CORRECTION_WINDOW_MINUTES", raising=False)

    module = _load_module_from_path(
        "sloths_inventory._settings_inventory_correction_window_default_test",
        sloths_inventory.settings.__file__,
    )
    assert module.INVENTORY_CORRECTION_WINDOW_MINUTES == 0


def test_settings_inventory_correction_window_minutes_can_be_overridden_via_env(
    tmp_path, monkeypatch
) -> None:
    """``INVENTORY_CORRECTION_WINDOW_MINUTES`` follows the integer env value."""

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("INVENTORY_CORRECTION_WINDOW_MINUTES", "25")

    module = _load_module_from_path(
        "sloths_inventory._settings_inventory_correction_window_override_test",
        sloths_inventory.settings.__file__,
    )
    assert module.INVENTORY_CORRECTION_WINDOW_MINUTES == 25


def test_settings_bool_env_var_empty_string_uses_default(tmp_path, monkeypatch) -> None:
    """Empty string for a bool env var should fall back to the declared default."""

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DEBUG", "")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")

    module = _load_module_from_path(
        "sloths_inventory._settings_bool_empty_string_test",
        sloths_inventory.settings.__file__,
    )
    assert module.DEBUG is False


def test_settings_secure_ssl_redirect_exempt(tmp_path, monkeypatch) -> None:
    """
    When SECURE_SSL_REDIRECT is truthy, settings should set
    SECURE_SSL_REDIRECT=True and define SECURE_REDIRECT_EXEMPT with the health path.
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DEBUG", "1")
    monkeypatch.setenv("SECRET_KEY", "dummy-secret")
    monkeypatch.setenv("SECURE_SSL_REDIRECT", "true")

    module = _load_module_from_path(
        "sloths_inventory._settings_secure_ssl_redirect_test",
        sloths_inventory.settings.__file__,
    )

    assert module.SECURE_SSL_REDIRECT is True
    assert hasattr(module, "SECURE_REDIRECT_EXEMPT")
    assert module.SECURE_REDIRECT_EXEMPT == [r"^health/"]


def test_settings_secure_flags_can_be_overridden_when_debug_false(
    tmp_path, monkeypatch
) -> None:
    """Security flags should remain env-driven in production mode."""

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DEBUG", "0")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("SECURE_SSL_REDIRECT", "1")
    monkeypatch.setenv("SESSION_COOKIE_SECURE", "yes")
    monkeypatch.setenv("CSRF_COOKIE_SECURE", "on")

    module = _load_module_from_path(
        "sloths_inventory._settings_secure_flags_debug_false_test",
        sloths_inventory.settings.__file__,
    )

    assert module.SECURE_SSL_REDIRECT is True
    assert module.SESSION_COOKIE_SECURE is True
    assert module.CSRF_COOKIE_SECURE is True
    assert module.SECURE_REDIRECT_EXEMPT == [r"^health/"]


def test_settings_secure_proxy_ssl_header_is_optional(tmp_path, monkeypatch) -> None:
    """SECURE_PROXY_SSL_HEADER should be configured only when both env parts exist."""

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DEBUG", "0")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("SECURE_PROXY_SSL_HEADER_NAME", "HTTP_X_FORWARDED_PROTO")
    monkeypatch.setenv("SECURE_PROXY_SSL_HEADER_VALUE", "https")

    module = _load_module_from_path(
        "sloths_inventory._settings_secure_proxy_header_test",
        sloths_inventory.settings.__file__,
    )

    assert module.SECURE_PROXY_SSL_HEADER == ("HTTP_X_FORWARDED_PROTO", "https")


def test_settings_secure_proxy_ssl_header_requires_both_parts(
    tmp_path, monkeypatch
) -> None:
    """A partial proxy header configuration should not create Django's tuple."""

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DEBUG", "0")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("SECURE_PROXY_SSL_HEADER_NAME", "HTTP_X_FORWARDED_PROTO")
    monkeypatch.delenv("SECURE_PROXY_SSL_HEADER_VALUE", raising=False)

    module = _load_module_from_path(
        "sloths_inventory._settings_partial_secure_proxy_header_test",
        sloths_inventory.settings.__file__,
    )

    assert not hasattr(module, "SECURE_PROXY_SSL_HEADER")
