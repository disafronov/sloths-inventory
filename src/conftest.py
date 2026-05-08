from __future__ import annotations

import os
from typing import Any, Generator

import pytest
from django.conf import settings

from catalogs.models import Location, Status
from devices.models import Device


# Autouse fixture to run each test under all supported locales
@pytest.fixture(autouse=True, params=[code for code, _ in settings.LANGUAGES])
def _set_locale(request: pytest.FixtureRequest) -> Generator[None, None, None]:
    from django.utils import translation

    translation.activate(request.param)
    yield
    translation.deactivate()


def _env_truthy(name: str) -> bool:
    return os.environ.get(name) in {"1", "true", "True"}


@pytest.fixture
def inventory_test_device(db: Any) -> Device:
    """
    Standard ``Device`` row with category/type/manufacturer/model for tests.

    Reduces duplicated catalog graph setup across inventory and related suites.
    """

    from devices.attributes import Category, Manufacturer, Model, Type

    category = Category.objects.create(name="Laptops")
    device_type = Type.objects.create(name="Laptop")
    manufacturer = Manufacturer.objects.create(name="ACME")
    device_model = Model.objects.create(name="Model X")
    return Device.objects.create(
        category=category,
        type=device_type,
        manufacturer=manufacturer,
        model=device_model,
    )


@pytest.fixture
def inventory_test_status_location(db: Any) -> dict[str, Location | Status]:
    """Typical ``Status`` and ``Location`` rows for inventory operation tests."""

    return {
        "status": Status.objects.create(name="In stock"),
        "location": Location.objects.create(name="Moscow"),
    }
