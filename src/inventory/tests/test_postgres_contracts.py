from __future__ import annotations

from datetime import datetime
from datetime import timezone as dt_timezone

import pytest
from django.contrib.auth.models import User
from django.test import Client

from catalogs.models import Location, Responsible, Status
from devices.attributes import Category, Manufacturer, Model, Type
from devices.models import Device
from inventory.models import Item, Operation

pytestmark = [pytest.mark.postgres]


def _make_device() -> Device:
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


@pytest.mark.django_db
def test_my_items_uses_id_tiebreaker_when_operations_share_created_at() -> None:
    device = _make_device()
    status = Status.objects.create(name="In stock")
    location = Location.objects.create(name="Moscow")

    user1 = User.objects.create_user(username="u1", password="pw")
    user2 = User.objects.create_user(username="u2", password="pw")
    resp1 = Responsible.objects.create(
        last_name="Ivanov", first_name="Ivan", user=user1
    )
    resp2 = Responsible.objects.create(
        last_name="Petrov", first_name="Petr", user=user2
    )

    item = Item.objects.create(inventory_number="INV-TIE", device=device)
    op1 = Operation.objects.create(
        item=item,
        status=status,
        responsible=resp1,
        location=location,
        notes="first",
    )
    op2 = Operation.objects.create(
        item=item,
        status=status,
        responsible=resp2,
        location=location,
        notes="second",
    )

    # Force identical timestamps and validate that "latest" is determined by id.
    ts = datetime(2026, 1, 1, 12, 0, 0, tzinfo=dt_timezone.utc)
    Operation.objects.filter(pk__in=[op1.pk, op2.pk]).update(created_at=ts)

    client = Client()
    client.force_login(user1)
    response = client.get("/")
    assert response.status_code == 200
    assert b"INV-TIE" not in response.content

    client.force_login(user2)
    response2 = client.get("/")
    assert response2.status_code == 200
    assert b"INV-TIE" in response2.content


@pytest.mark.django_db
def test_previous_items_ordering_by_last_on_me_created_at_is_stable() -> None:
    device = _make_device()
    status = Status.objects.create(name="In stock")
    location = Location.objects.create(name="Moscow")

    user1 = User.objects.create_user(username="u1", password="pw")
    user2 = User.objects.create_user(username="u2", password="pw")
    resp1 = Responsible.objects.create(
        last_name="Ivanov", first_name="Ivan", user=user1
    )
    resp2 = Responsible.objects.create(
        last_name="Petrov", first_name="Petr", user=user2
    )

    item_older = Item.objects.create(inventory_number="INV-OLD", device=device)
    item_newer = Item.objects.create(inventory_number="INV-NEW", device=device)

    # Both items used to belong to resp1, then were transferred away.
    op_old_mine = Operation.objects.create(
        item=item_older,
        status=status,
        responsible=resp1,
        location=location,
        notes="old-mine",
    )
    Operation.objects.create(
        item=item_older,
        status=status,
        responsible=resp2,
        location=location,
        notes="old-away",
    )
    op_new_mine = Operation.objects.create(
        item=item_newer,
        status=status,
        responsible=resp1,
        location=location,
        notes="new-mine",
    )
    Operation.objects.create(
        item=item_newer,
        status=status,
        responsible=resp2,
        location=location,
        notes="new-away",
    )

    # Control ordering deterministically via created_at timestamps.
    older_ts = datetime(2026, 1, 1, 10, 0, 0, tzinfo=dt_timezone.utc)
    newer_ts = datetime(2026, 1, 1, 11, 0, 0, tzinfo=dt_timezone.utc)
    Operation.objects.filter(pk=op_old_mine.pk).update(created_at=older_ts)
    Operation.objects.filter(pk=op_new_mine.pk).update(created_at=newer_ts)

    client = Client()
    client.force_login(user1)
    response = client.get("/previous/")
    assert response.status_code == 200

    body = response.content
    pos_new = body.find(b"INV-NEW")
    pos_old = body.find(b"INV-OLD")
    assert pos_new != -1
    assert pos_old != -1
    assert pos_new < pos_old, "Newer previously-owned item should be listed first"
