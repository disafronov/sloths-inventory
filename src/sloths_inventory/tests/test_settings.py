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

    with pytest.raises(ImproperlyConfigured, match="SECRET_KEY must be set"):
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
    ``INVENTORY_CORRECTION_WINDOW_MINUTES`` defaults to 10 when the env var is absent.

    Uses an isolated CWD so ``environ.Env.read_env()`` does not pick up a repo-local
    ``.env`` while importing ``settings.py``.
    """

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("INVENTORY_CORRECTION_WINDOW_MINUTES", raising=False)

    module = _load_module_from_path(
        "sloths_inventory._settings_inventory_correction_window_default_test",
        sloths_inventory.settings.__file__,
    )
    assert module.INVENTORY_CORRECTION_WINDOW_MINUTES == 10


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
