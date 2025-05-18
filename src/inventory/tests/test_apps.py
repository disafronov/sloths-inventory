"""Тесты конфигурации приложения inventory."""

import os
from pathlib import Path

import pytest
from django.apps import apps

from inventory.apps import InventoryConfig


def test_inventory_config():
    """Тест конфигурации InventoryConfig."""
    app_config = apps.get_app_config("inventory")
    assert isinstance(app_config, InventoryConfig)
    assert app_config.name == "inventory"
    assert app_config.verbose_name == "Инвентарь"
    assert app_config.default_auto_field == "django.db.models.BigAutoField"
    assert app_config.path == os.path.join(os.path.dirname(os.path.dirname(__file__))) 