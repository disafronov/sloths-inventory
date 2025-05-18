"""Tests for devices app configuration."""

import os
from pathlib import Path

import pytest
from django.apps import apps

from devices.apps import DevicesConfig


def test_devices_config():
    """Test DevicesConfig configuration."""
    app_config = apps.get_app_config("devices")
    assert isinstance(app_config, DevicesConfig)
    assert app_config.name == "devices"
    assert app_config.verbose_name == "Устройства"
    assert app_config.default_auto_field == "django.db.models.BigAutoField"
    assert app_config.path == os.path.join(os.path.dirname(os.path.dirname(__file__))) 