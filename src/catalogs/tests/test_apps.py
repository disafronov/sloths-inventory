"""Тесты конфигурации приложения catalogs."""

import os
from pathlib import Path

import pytest
from django.apps import apps

from catalogs.apps import CatalogsConfig


def test_catalogs_config():
    """Тест конфигурации CatalogsConfig."""
    app_config = apps.get_app_config("catalogs")
    assert isinstance(app_config, CatalogsConfig)
    assert app_config.name == "catalogs"
    assert app_config.verbose_name == "Каталоги"
    assert app_config.default_auto_field == "django.db.models.BigAutoField"
    assert app_config.path == os.path.join(os.path.dirname(os.path.dirname(__file__))) 