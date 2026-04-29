import pytest
from django.contrib.auth.models import AnonymousUser, User
from django.test import Client, RequestFactory

from catalogs.models import Location, Responsible, Status
from devices.attributes import Category, Manufacturer, Model, Type
from devices.models import Device
from inventory.models import Item, Operation
from inventory.views import _get_responsible_for_user


@pytest.mark.django_db
def test_my_items_requires_login() -> None:
    client = Client()
    response = client.get("/")
    assert response.status_code == 302
    assert "/login/" in response["Location"]


def test_get_responsible_for_user_returns_none_for_anonymous() -> None:
    rf = RequestFactory()
    request = rf.get("/")
    request.user = AnonymousUser()
    assert _get_responsible_for_user(request) is None


@pytest.mark.django_db
def test_my_items_empty_when_user_has_no_responsible() -> None:
    user = User.objects.create_user(username="alice", password="pw")

    client = Client()
    client.force_login(user)

    response = client.get("/")
    assert response.status_code == 200
    assert (
        b"not linked" in response.content
        or "не привязан к профилю ответственного".encode("utf-8") in response.content
    )


@pytest.mark.django_db
def test_my_items_shows_only_items_where_latest_operation_has_my_responsible() -> None:
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

    user1 = User.objects.create_user(username="u1", password="pw")
    user2 = User.objects.create_user(username="u2", password="pw")
    resp1 = Responsible.objects.create(
        last_name="Ivanov", first_name="Ivan", user=user1
    )
    resp2 = Responsible.objects.create(
        last_name="Petrov", first_name="Petr", user=user2
    )

    item_mine = Item.objects.create(inventory_number="INV-MINE", device=device)
    item_not_mine = Item.objects.create(inventory_number="INV-NOT-MINE", device=device)
    item_transferred_away = Item.objects.create(
        inventory_number="INV-AWAY", device=device
    )
    Item.objects.create(inventory_number="INV-NO-OPS", device=device)

    Operation.objects.create(
        item=item_mine, status=status, responsible=resp1, location=location
    )
    Operation.objects.create(
        item=item_not_mine, status=status, responsible=resp2, location=location
    )
    Operation.objects.create(
        item=item_transferred_away, status=status, responsible=resp1, location=location
    )
    Operation.objects.create(
        item=item_transferred_away, status=status, responsible=resp2, location=location
    )

    client = Client()
    client.force_login(user1)

    response = client.get("/")
    assert response.status_code == 200

    assert b"INV-MINE" in response.content
    assert b"INV-NOT-MINE" not in response.content
    assert b"INV-AWAY" not in response.content
    assert b"INV-NO-OPS" not in response.content


@pytest.mark.django_db
def test_item_history_only_for_my_item() -> None:
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

    user1 = User.objects.create_user(username="u1", password="pw")
    user2 = User.objects.create_user(username="u2", password="pw")
    resp1 = Responsible.objects.create(
        last_name="Ivanov", first_name="Ivan", user=user1
    )
    resp2 = Responsible.objects.create(
        last_name="Petrov", first_name="Petr", user=user2
    )

    item_mine = Item.objects.create(inventory_number="INV-MINE", device=device)
    item_other = Item.objects.create(inventory_number="INV-OTHER", device=device)

    Operation.objects.create(
        item=item_mine, status=status, responsible=resp1, location=location, notes="1"
    )
    Operation.objects.create(
        item=item_mine, status=status, responsible=resp1, location=location, notes="2"
    )
    Operation.objects.create(
        item=item_other, status=status, responsible=resp2, location=location, notes="x"
    )

    client = Client()
    client.force_login(user1)

    ok = client.get(f"/items/{item_mine.pk}/")
    assert ok.status_code == 200
    assert b"INV-MINE" in ok.content

    forbidden = client.get(f"/items/{item_other.pk}/")
    assert forbidden.status_code == 404
