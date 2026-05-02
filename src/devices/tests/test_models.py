"""Tests for ``devices.models`` and ``devices.attributes`` catalog usage hooks."""

from typing import Any

import pytest

from devices.attributes import Category, Manufacturer, Model, Type
from devices.models import Device
from inventory.models import Item


@pytest.mark.django_db
def test_device_attribute_is_catalog_reference_in_use_adding_and_referenced() -> None:
    """Unsaved attribute rows short-circuit; saved rows query ``Device`` references."""

    cases: list[tuple[type[Any], str]] = [
        (Category, "Cat-ref"),
        (Type, "Typ-ref"),
        (Manufacturer, "Mfr-ref"),
        (Model, "Mdl-ref"),
    ]

    for model_cls, prefix in cases:
        row = model_cls(name=f"{prefix}-unsaved")
        assert row.is_catalog_reference_in_use() is False

        ref = model_cls.objects.create(name=f"{prefix}-saved")
        cat = Category.objects.create(name=f"{prefix}-c")
        typ = Type.objects.create(name=f"{prefix}-t")
        mfr = Manufacturer.objects.create(name=f"{prefix}-m")
        mdl = Model.objects.create(name=f"{prefix}-d")
        Device.objects.create(
            category=cat if model_cls is not Category else ref,
            type=typ if model_cls is not Type else ref,
            manufacturer=mfr if model_cls is not Manufacturer else ref,
            model=mdl if model_cls is not Model else ref,
        )
        assert ref.is_catalog_reference_in_use() is True


@pytest.mark.django_db
def test_device_is_catalog_reference_in_use_adding_and_with_item() -> None:
    """``Device`` rows short-circuit while adding; referenced by ``Item`` when saved."""

    category = Category.objects.create(name="Laptops")
    device_type = Type.objects.create(name="Laptop")
    manufacturer = Manufacturer.objects.create(name="ACME")
    device_model = Model.objects.create(name="Model X")
    device = Device(
        category=category,
        type=device_type,
        manufacturer=manufacturer,
        model=device_model,
    )
    assert device.is_catalog_reference_in_use() is False

    device.save()
    assert device.is_catalog_reference_in_use() is False

    Item.objects.create(inventory_number="INV-DEV-USE", device=device)
    assert device.is_catalog_reference_in_use() is True
