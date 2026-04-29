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
