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

    response_prev = client.get("/previous/")
    assert response_prev.status_code == 302
    assert "/login/" in response_prev["Location"]


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
def test_item_history_only_for_my_or_previously_my_item() -> None:
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
    item_previously_mine = Item.objects.create(
        inventory_number="INV-PREV", device=device
    )

    Operation.objects.create(
        item=item_mine, status=status, responsible=resp1, location=location, notes="1"
    )
    Operation.objects.create(
        item=item_mine, status=status, responsible=resp1, location=location, notes="2"
    )
    Operation.objects.create(
        item=item_other, status=status, responsible=resp2, location=location, notes="x"
    )
    op_prev_1 = Operation.objects.create(
        item=item_previously_mine,
        status=status,
        responsible=resp1,
        location=location,
        notes="prev-1",
    )
    op_prev_2 = Operation.objects.create(
        item=item_previously_mine,
        status=status,
        responsible=resp2,
        location=location,
        notes="prev-2",
    )

    client = Client()
    client.force_login(user1)

    ok = client.get(f"/items/{item_mine.pk}/")
    assert ok.status_code == 200
    assert b"INV-MINE" in ok.content

    forbidden = client.get(f"/items/{item_other.pk}/")
    assert forbidden.status_code == 404

    previously_ok = client.get(f"/items/{item_previously_mine.pk}/")
    assert previously_ok.status_code == 200
    # Former owners can see history until their last responsibility plus one handoff op.
    assert op_prev_1.notes.encode("utf-8") in previously_ok.content
    assert op_prev_2.notes.encode("utf-8") in previously_ok.content


@pytest.mark.django_db
def test_previous_items_shows_only_items_where_user_was_responsible_in_the_past() -> (
    None
):
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

    item_current = Item.objects.create(inventory_number="INV-CUR", device=device)
    item_previous = Item.objects.create(inventory_number="INV-PREV", device=device)
    item_never = Item.objects.create(inventory_number="INV-NEVER", device=device)

    Operation.objects.create(
        item=item_current, status=status, responsible=resp1, location=location
    )
    Operation.objects.create(
        item=item_previous, status=status, responsible=resp1, location=location
    )
    Operation.objects.create(
        item=item_previous, status=status, responsible=resp2, location=location
    )

    client = Client()
    client.force_login(user1)

    response = client.get("/previous/")
    assert response.status_code == 200
    assert b"INV-PREV" in response.content
    assert b"INV-CUR" not in response.content
    assert item_never.inventory_number.encode("utf-8") not in response.content


@pytest.mark.django_db
def test_item_history_for_former_owner_includes_only_one_handoff_after_last_mine() -> (
    None
):
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
    user3 = User.objects.create_user(username="u3", password="pw")
    resp1 = Responsible.objects.create(
        last_name="Ivanov", first_name="Ivan", user=user1
    )
    resp2 = Responsible.objects.create(
        last_name="Petrov", first_name="Petr", user=user2
    )
    resp3 = Responsible.objects.create(
        last_name="Sidorov", first_name="Sid", user=user3
    )

    item = Item.objects.create(inventory_number="INV-LIMIT", device=device)
    Operation.objects.create(
        item=item, status=status, responsible=resp1, location=location, notes="a"
    )
    Operation.objects.create(
        item=item, status=status, responsible=resp2, location=location, notes="b1"
    )
    last_mine = Operation.objects.create(
        item=item, status=status, responsible=resp2, location=location, notes="b2"
    )
    handoff = Operation.objects.create(
        item=item, status=status, responsible=resp3, location=location, notes="c1"
    )
    Operation.objects.create(
        item=item, status=status, responsible=resp3, location=location, notes="c2"
    )

    client = Client()
    client.force_login(user2)

    response = client.get(f"/items/{item.pk}/")
    assert response.status_code == 200
    assert b"INV-LIMIT" in response.content
    assert b"a" in response.content
    assert last_mine.notes.encode("utf-8") in response.content
    assert handoff.notes.encode("utf-8") in response.content
    assert b"c2" not in response.content
