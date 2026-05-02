"""
Tests for ``resolve_item_history_context`` edge cases in ``inventory.models.pages``.
"""

from unittest.mock import MagicMock, patch

import pytest

from catalogs.models import Location, Responsible, Status
from devices.attributes import Category, Manufacturer, Model, Type
from devices.models import Device
from inventory.models import (
    Item,
    Operation,
    PendingTransfer,
    resolve_item_history_context,
)


@pytest.mark.django_db
def test_resolve_item_history_pending_receiver_no_operations() -> None:
    """
    Receiver path loads the ``Item`` but an empty operation stream yields ``None``.

    Defensive: normal flows have operations before a pending offer exists.
    """

    category = Category.objects.create(name="Laptops")
    device_type = Type.objects.create(name="Laptop")
    manufacturer = Manufacturer.objects.create(name="ACME")
    device_model = Model.objects.create(name="Model X")
    device = Device.objects.create(
        category=category,
        type=device_type,
        manufacturer=manufacturer,
        model=device_model,
    )
    status = Status.objects.create(name="In stock")
    location = Location.objects.create(name="Moscow")
    owner = Responsible.objects.create(last_name="Own", first_name="Er")
    receiver = Responsible.objects.create(last_name="Recv", first_name="Er")

    item = Item.objects.create(inventory_number="INV-RES-NOOP", device=device)
    Operation.objects.create(
        item=item,
        status=status,
        responsible=owner,
        location=location,
    )
    PendingTransfer.objects.create(
        item=item,
        from_responsible=owner,
        to_responsible=receiver,
        notes="",
    )
    Operation.objects.filter(item=item).delete()

    assert resolve_item_history_context(receiver, item.pk) is None


@pytest.mark.django_db
def test_resolve_item_history_former_owner_item_get_miss() -> None:
    """
    Former-owner branch calls ``Item.objects.with_device_relations().get``; a miss
    maps to ``None`` (same HTTP outcome as unknown items).
    """

    category = Category.objects.create(name="Laptops")
    device_type = Type.objects.create(name="Laptop")
    manufacturer = Manufacturer.objects.create(name="ACME")
    device_model = Model.objects.create(name="Model X")
    device = Device.objects.create(
        category=category,
        type=device_type,
        manufacturer=manufacturer,
        model=device_model,
    )
    status = Status.objects.create(name="In stock")
    location = Location.objects.create(name="Moscow")
    former = Responsible.objects.create(last_name="Former", first_name="Own")
    new_owner = Responsible.objects.create(last_name="New", first_name="Own")

    item = Item.objects.create(inventory_number="INV-RES-DEL", device=device)
    Operation.objects.create(
        item=item,
        status=status,
        responsible=former,
        location=location,
    )
    Operation.objects.create(
        item=item,
        status=status,
        responsible=new_owner,
        location=location,
    )

    mqs = MagicMock()
    mqs.get.side_effect = Item.DoesNotExist
    with patch.object(Item.objects, "with_device_relations", return_value=mqs):
        assert resolve_item_history_context(former, item.pk) is None
