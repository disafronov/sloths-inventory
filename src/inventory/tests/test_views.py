from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth.models import AnonymousUser, User
from django.core.exceptions import ValidationError
from django.test import Client, RequestFactory, override_settings
from django.urls import reverse
from django.utils import timezone

from catalogs.models import Location, Responsible, Status
from devices.attributes import Category, Manufacturer, Model, Type
from devices.models import Device
from inventory.models import Item, Operation, PendingTransfer
from inventory.presentation import validation_error_user_message


@pytest.mark.django_db
def test_my_items_requires_login() -> None:
    client = Client()
    response = client.get("/")
    assert response.status_code == 302
    assert "/login/" in response["Location"]

    response_prev = client.get("/previous/")
    assert response_prev.status_code == 302
    assert "/login/" in response_prev["Location"]


def test_linked_profile_for_user_returns_none_for_anonymous() -> None:
    rf = RequestFactory()
    request = rf.get("/")
    request.user = AnonymousUser()
    assert Responsible.linked_profile_for_user(request.user) is None


def test_validation_error_user_message_single_string() -> None:
    assert validation_error_user_message(ValidationError("one thing")) == "one thing"


def test_validation_error_user_message_list_joins_messages() -> None:
    exc = ValidationError(["first problem", "second problem"])
    assert validation_error_user_message(exc) == "first problem; second problem"


def test_validation_error_user_message_message_dict_flattens_fields() -> None:
    exc = ValidationError({"field_a": ["x"], "field_b": ["y", "z"]})
    out = validation_error_user_message(exc)
    assert "field_a: x" in out
    assert "field_b: y" in out
    assert "field_b: z" in out


def test_validation_error_user_message_fallback_uses_str_when_no_messages() -> None:
    """``str(exc)`` path when ``message_dict`` is empty and ``messages`` is empty."""

    class NonDictValidationPayload:
        """Minimal stand-in: helpers only use ``getattr`` (not ``isinstance``)."""

        message_dict: dict = {}
        messages: list = []

        def __str__(self) -> str:
            return "fallback-body"

    assert validation_error_user_message(NonDictValidationPayload()) == "fallback-body"


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

    response_prev = client.get("/previous/")
    assert response_prev.status_code == 200
    assert (
        b"not linked" in response_prev.content
        or "не привязан к профилю ответственного".encode("utf-8")
        in response_prev.content
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
def test_build_my_items_owned_list_does_not_query_per_row_for_location_status() -> None:
    """
    Owned rows on the My items page must not N+1 when templates read
    ``current_location`` / ``current_status`` (SQL annotations shadow descriptors).
    """

    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    from inventory.models import build_my_items_page_data

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

    user = User.objects.create_user(username="u_nplus", password="pw")
    resp = Responsible.objects.create(last_name="Nplus", first_name="One", user=user)

    for i in range(25):
        item = Item.objects.create(inventory_number=f"INV-NP-{i:03d}", device=device)
        Operation.objects.create(
            item=item, status=status, responsible=resp, location=location
        )

    with CaptureQueriesContext(connection) as ctx:
        page = build_my_items_page_data(resp, query="", list_kind="owned")
        for row in page.items:
            assert row.current_location == location.name
            assert row.current_status == status.name

    assert len(ctx.captured_queries) <= 12, (
        "Expected a bounded number of SQL statements when resolving many owned "
        f"rows (got {len(ctx.captured_queries)})"
    )


@pytest.mark.django_db
def test_my_items_search_filters_by_inventory_number_and_serial() -> None:
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

    user = User.objects.create_user(username="u1", password="pw")
    resp = Responsible.objects.create(last_name="Ivanov", first_name="Ivan", user=user)

    item1 = Item.objects.create(
        inventory_number="INV-ABC-1", device=device, serial_number="SN-123"
    )
    item2 = Item.objects.create(
        inventory_number="INV-XYZ-2", device=device, serial_number="SN-999"
    )
    Operation.objects.create(
        item=item1, status=status, responsible=resp, location=location
    )
    Operation.objects.create(
        item=item2, status=status, responsible=resp, location=location
    )

    client = Client()
    client.force_login(user)

    by_inv = client.get("/", {"q": "ABC"})
    assert by_inv.status_code == 200
    assert b"INV-ABC-1" in by_inv.content
    assert b"INV-XYZ-2" not in by_inv.content

    by_serial = client.get("/", {"q": "SN-999"})
    assert by_serial.status_code == 200
    assert b"INV-ABC-1" not in by_serial.content
    assert b"INV-XYZ-2" in by_serial.content


@pytest.mark.django_db
def test_my_items_list_kind_outgoing_shows_only_outgoing_card() -> None:
    """`kind=outgoing` must list only outgoing transfer cards, not owned rows."""

    user_sender = User.objects.create_user(username="sender", password="pw")
    user_receiver = User.objects.create_user(username="receiver", password="pw")
    resp_sender = Responsible.objects.create(
        last_name="Sender", first_name="User", user=user_sender
    )
    resp_receiver = Responsible.objects.create(
        last_name="Receiver", first_name="User", user=user_receiver
    )
    status = Status.objects.create(name="In use")
    location = Location.objects.create(name="Home")
    item_xfer = _make_item_with_operation(
        status, location, resp_sender, "INV-KIND-OUT-ONLY"
    )
    PendingTransfer.objects.create(
        item=item_xfer,
        from_responsible=resp_sender,
        to_responsible=resp_receiver,
    )

    client = Client()
    client.force_login(user_sender)

    owned_resp = client.get("/", {"kind": "owned"})
    assert owned_resp.status_code == 200
    assert b"INV-KIND-OUT-ONLY" not in owned_resp.content

    outgoing_resp = client.get("/", {"kind": "outgoing"})
    assert outgoing_resp.status_code == 200
    assert b"INV-KIND-OUT-ONLY" in outgoing_resp.content
    assert (
        outgoing_resp.content.count(b'class="item-card item-card--outgoing-transfer"')
        == 1
    )

    all_resp = client.get("/")
    assert all_resp.status_code == 200
    assert b"INV-KIND-OUT-ONLY" in all_resp.content


@pytest.mark.django_db
def test_my_items_list_kind_owned_hides_transfer_offers() -> None:
    """
    `kind=owned` must not show inventory numbers that appear only on transfer cards.
    """

    user_sender = User.objects.create_user(username="sender", password="pw")
    user_receiver = User.objects.create_user(username="receiver", password="pw")
    resp_sender = Responsible.objects.create(
        last_name="Sender", first_name="User", user=user_sender
    )
    resp_receiver = Responsible.objects.create(
        last_name="Receiver", first_name="User", user=user_receiver
    )
    status = Status.objects.create(name="In use")
    location = Location.objects.create(name="Home")
    _make_item_with_operation(status, location, resp_sender, "INV-KIND-OWN-PLAIN")
    item_out = _make_item_with_operation(
        status, location, resp_sender, "INV-KIND-OWN-XFER"
    )
    PendingTransfer.objects.create(
        item=item_out,
        from_responsible=resp_sender,
        to_responsible=resp_receiver,
    )

    client = Client()
    client.force_login(user_sender)

    owned_resp = client.get("/", {"kind": "owned"})
    assert owned_resp.status_code == 200
    assert b"INV-KIND-OWN-PLAIN" in owned_resp.content
    assert b"INV-KIND-OWN-XFER" not in owned_resp.content

    all_resp = client.get("/")
    assert all_resp.status_code == 200
    assert b"INV-KIND-OWN-PLAIN" in all_resp.content
    assert b"INV-KIND-OWN-XFER" in all_resp.content


@pytest.mark.django_db
def test_my_items_list_kind_incoming_for_receiver() -> None:
    """Receiver: `kind=incoming` shows the offer; `kind=outgoing` is empty."""

    user_sender = User.objects.create_user(username="sender", password="pw")
    user_receiver = User.objects.create_user(username="receiver", password="pw")
    resp_sender = Responsible.objects.create(
        last_name="Sender", first_name="User", user=user_sender
    )
    resp_receiver = Responsible.objects.create(
        last_name="Receiver", first_name="User", user=user_receiver
    )
    status = Status.objects.create(name="In use")
    location = Location.objects.create(name="Home")
    item = _make_item_with_operation(status, location, resp_sender, "INV-KIND-INCOMING")
    PendingTransfer.objects.create(
        item=item,
        from_responsible=resp_sender,
        to_responsible=resp_receiver,
    )

    client = Client()
    client.force_login(user_receiver)

    incoming_resp = client.get("/", {"kind": "incoming"})
    assert incoming_resp.status_code == 200
    assert b"INV-KIND-INCOMING" in incoming_resp.content

    outgoing_resp = client.get("/", {"kind": "outgoing"})
    assert outgoing_resp.status_code == 200
    assert b"INV-KIND-INCOMING" not in outgoing_resp.content


@pytest.mark.django_db
def test_my_items_list_kind_invalid_falls_back_to_all() -> None:
    """Unknown `kind` values are ignored (treated as all)."""

    user_sender = User.objects.create_user(username="sender", password="pw")
    user_receiver = User.objects.create_user(username="receiver", password="pw")
    resp_sender = Responsible.objects.create(
        last_name="Sender", first_name="User", user=user_sender
    )
    resp_receiver = Responsible.objects.create(
        last_name="Receiver", first_name="User", user=user_receiver
    )
    status = Status.objects.create(name="In use")
    location = Location.objects.create(name="Home")
    item = _make_item_with_operation(status, location, resp_sender, "INV-KIND-INVALID")
    PendingTransfer.objects.create(
        item=item,
        from_responsible=resp_sender,
        to_responsible=resp_receiver,
    )

    client = Client()
    client.force_login(user_sender)

    baseline = client.get("/")
    weird = client.get("/", {"kind": "not-a-real-kind"})
    assert baseline.status_code == 200
    assert weird.status_code == 200
    assert b"INV-KIND-INVALID" in baseline.content
    assert b"INV-KIND-INVALID" in weird.content
    assert baseline.content.count(
        b'class="item-card item-card--outgoing-transfer"'
    ) == weird.content.count(b'class="item-card item-card--outgoing-transfer"')


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
def test_previous_items_search_filters_results() -> None:
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

    item_a = Item.objects.create(
        inventory_number="INV-SEARCH-A", device=device, serial_number="S-A"
    )
    item_b = Item.objects.create(
        inventory_number="INV-SEARCH-B", device=device, serial_number="S-B"
    )
    Operation.objects.create(
        item=item_a, status=status, responsible=resp1, location=location
    )
    Operation.objects.create(
        item=item_a, status=status, responsible=resp2, location=location
    )
    Operation.objects.create(
        item=item_b, status=status, responsible=resp1, location=location
    )
    Operation.objects.create(
        item=item_b, status=status, responsible=resp2, location=location
    )

    client = Client()
    client.force_login(user1)

    response = client.get("/previous/", {"q": "SEARCH-A"})
    assert response.status_code == 200
    assert b"INV-SEARCH-A" in response.content
    assert b"INV-SEARCH-B" not in response.content


@pytest.mark.django_db
def test_previous_items_incoming_transfer_uses_transfer_card_once() -> None:
    """
    Active pending offers for items on the "Previously my items" list reuse the same
    transfer card as "My items" (tint + party plaque); the item is not duplicated as
    a plain row.
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

    user_former = User.objects.create_user(username="u_prev_xfer", password="pw")
    user_current = User.objects.create_user(username="u_curr_xfer", password="pw")
    resp_former = Responsible.objects.create(
        last_name="Former", first_name="X", user=user_former
    )
    resp_current = Responsible.objects.create(
        last_name="Current", first_name="Y", user=user_current
    )

    item = Item.objects.create(inventory_number="INV-PREV-XFER-LIST", device=device)
    Operation.objects.create(
        item=item, status=status, responsible=resp_former, location=location
    )
    Operation.objects.create(
        item=item, status=status, responsible=resp_current, location=location
    )
    PendingTransfer.objects.create(
        item=item, from_responsible=resp_current, to_responsible=resp_former
    )

    client = Client()
    client.force_login(user_former)
    response = client.get("/previous/")
    assert response.status_code == 200
    assert b"item-card--incoming-transfer" in response.content
    inv = item.inventory_number.encode("utf-8")
    assert response.content.count(inv) == 1


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
    # Avoid false positives: "c2" may occur in CSRF tokens. We assert the note value
    # isn't rendered as a standalone text node.
    assert b">c2<" not in response.content


def _make_item_with_operation(
    status: "Status",
    location: "Location",
    responsible: "Responsible",
    inventory_number: str = "INV-TEST",
) -> "Item":
    category = Category.objects.create(name=f"Cat-{inventory_number}")
    device_type = Type.objects.create(name=f"Type-{inventory_number}")
    manufacturer = Manufacturer.objects.create(name=f"Mfr-{inventory_number}")
    device_model = Model.objects.create(name=f"Model-{inventory_number}")
    device = Device.objects.create(
        category=category,
        type=device_type,
        manufacturer=manufacturer,
        model=device_model,
    )
    item = Item.objects.create(inventory_number=inventory_number, device=device)
    Operation.objects.create(
        item=item, status=status, responsible=responsible, location=location
    )
    return item


def _accept_journal_baseline_post(item: Item) -> dict[str, str]:
    """POST fields for ``accept_transfer`` (``journal_head_operation_id``)."""

    head_id = Operation.latest_operation_id_for_item(item.pk)
    assert head_id is not None
    return {"journal_head_operation_id": str(head_id)}


@pytest.mark.django_db
def test_change_location_requires_login() -> None:
    client = Client()
    response = client.get("/items/1/change-location/")
    assert response.status_code == 302
    assert "/login/" in response["Location"]


@pytest.mark.django_db
def test_change_location_returns_404_if_no_responsible() -> None:
    user = User.objects.create_user(username="alice", password="pw")
    status = Status.objects.create(name="In use")
    location = Location.objects.create(name="Home")
    resp = Responsible.objects.create(last_name="Other", first_name="User")
    item = _make_item_with_operation(status, location, resp, "INV-404")

    client = Client()
    client.force_login(user)
    response = client.get(f"/items/{item.pk}/change-location/")
    assert response.status_code == 404


@pytest.mark.django_db
def test_change_location_returns_404_if_not_current_owner() -> None:
    user1 = User.objects.create_user(username="u1", password="pw")
    user2 = User.objects.create_user(username="u2", password="pw")
    resp1 = Responsible.objects.create(last_name="One", first_name="User", user=user1)
    resp2 = Responsible.objects.create(last_name="Two", first_name="User", user=user2)
    status = Status.objects.create(name="In use")
    location = Location.objects.create(name="Home")
    item = _make_item_with_operation(status, location, resp2, "INV-NOTMINE")

    client = Client()
    client.force_login(user1)
    response = client.get(f"/items/{item.pk}/change-location/")
    assert response.status_code == 404

    # resp1 is unused but defined — suppress linter
    _ = resp1


@pytest.mark.django_db
def test_change_location_get_shows_form_with_locations() -> None:
    user = User.objects.create_user(username="u1", password="pw")
    resp = Responsible.objects.create(last_name="One", first_name="User", user=user)
    status = Status.objects.create(name="In use")
    location = Location.objects.create(name="Home")
    Location.objects.create(name="Dacha")
    item = _make_item_with_operation(status, location, resp, "INV-FORM")

    client = Client()
    client.force_login(user)
    response = client.get(f"/items/{item.pk}/change-location/")
    assert response.status_code == 200
    assert b"Home" in response.content
    assert b"Dacha" in response.content


@pytest.mark.django_db
def test_change_location_post_creates_new_operation_and_redirects() -> None:
    user = User.objects.create_user(username="u1", password="pw")
    resp = Responsible.objects.create(last_name="One", first_name="User", user=user)
    status = Status.objects.create(name="In use")
    location_old = Location.objects.create(name="Home")
    location_new = Location.objects.create(name="Dacha")
    item = _make_item_with_operation(status, location_old, resp, "INV-POST")

    assert item.operation_set.count() == 1

    client = Client()
    client.force_login(user)
    response = client.post(
        f"/items/{item.pk}/change-location/",
        {"location_id": location_new.pk},
    )
    assert response.status_code == 302
    assert response["Location"] == f"/items/{item.pk}/"

    assert item.operation_set.count() == 2
    latest = item.operation_set.order_by("-created_at", "-id").first()
    assert latest is not None
    assert latest.location == location_new
    assert latest.status == status
    assert latest.responsible == resp


@pytest.mark.django_db
def test_change_location_post_returns_404_when_location_id_is_missing() -> None:
    user = User.objects.create_user(username="u1", password="pw")
    resp = Responsible.objects.create(last_name="One", first_name="User", user=user)
    status = Status.objects.create(name="In use")
    location = Location.objects.create(name="Home")
    item = _make_item_with_operation(status, location, resp, "INV-NOLOCID")

    client = Client()
    client.force_login(user)
    response = client.post(f"/items/{item.pk}/change-location/", {})
    assert response.status_code == 400


@pytest.mark.django_db
def test_change_location_post_returns_404_for_invalid_location() -> None:
    user = User.objects.create_user(username="u1", password="pw")
    resp = Responsible.objects.create(last_name="One", first_name="User", user=user)
    status = Status.objects.create(name="In use")
    location = Location.objects.create(name="Home")
    item = _make_item_with_operation(status, location, resp, "INV-BADLOC")

    client = Client()
    client.force_login(user)
    response = client.post(
        f"/items/{item.pk}/change-location/",
        {"location_id": 99999},
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_change_location_post_returns_400_when_location_is_unchanged() -> None:
    user = User.objects.create_user(username="u1", password="pw")
    resp = Responsible.objects.create(last_name="One", first_name="User", user=user)
    status = Status.objects.create(name="In use")
    location = Location.objects.create(name="Home")
    item = _make_item_with_operation(status, location, resp, "INV-SAMELOC")

    client = Client()
    client.force_login(user)
    response = client.post(
        f"/items/{item.pk}/change-location/",
        {"location_id": location.pk},
    )
    assert response.status_code == 400
    assert item.operation_set.count() == 1


@pytest.mark.django_db
def test_create_transfer_requires_login() -> None:
    client = Client()
    response = client.get("/items/1/transfer/")
    assert response.status_code == 302
    assert "/login/" in response["Location"]


@pytest.mark.django_db
def test_create_transfer_returns_404_if_user_has_no_responsible() -> None:
    user = User.objects.create_user(username="u1", password="pw")
    client = Client()
    client.force_login(user)
    response = client.get("/items/1/transfer/")
    assert response.status_code == 404


@pytest.mark.django_db
def test_create_transfer_returns_404_if_not_current_owner() -> None:
    user1 = User.objects.create_user(username="u1", password="pw")
    user2 = User.objects.create_user(username="u2", password="pw")
    resp1 = Responsible.objects.create(last_name="One", first_name="User", user=user1)
    resp2 = Responsible.objects.create(last_name="Two", first_name="User", user=user2)
    status = Status.objects.create(name="In use")
    location = Location.objects.create(name="Home")
    item = _make_item_with_operation(status, location, resp2, "INV-XFER-404")

    client = Client()
    client.force_login(user1)
    response = client.get(f"/items/{item.pk}/transfer/")
    assert response.status_code == 404

    _ = resp1


@pytest.mark.django_db
def test_create_transfer_get_shows_receiver_options() -> None:
    user1 = User.objects.create_user(username="u1", password="pw")
    user2 = User.objects.create_user(username="u2", password="pw")
    resp1 = Responsible.objects.create(last_name="One", first_name="User", user=user1)
    resp2 = Responsible.objects.create(last_name="Two", first_name="User", user=user2)
    status = Status.objects.create(name="In use")
    location = Location.objects.create(name="Home")
    item = _make_item_with_operation(status, location, resp1, "INV-XFER-GET")

    client = Client()
    client.force_login(user1)
    response = client.get(f"/items/{item.pk}/transfer/")
    assert response.status_code == 200
    assert resp2.last_name.encode("utf-8") in response.content
    # The hint should not mention server time (UI wording detail).
    assert b"server time" not in response.content.lower()


@pytest.mark.django_db
@override_settings(INVENTORY_PENDING_TRANSFER_EXPIRATION_HOURS=0)
def test_create_transfer_get_hides_expiry_hint_when_disabled() -> None:
    """No automatic expiry hint when the configured window is zero."""

    user1 = User.objects.create_user(username="u1z", password="pw")
    user2 = User.objects.create_user(username="u2z", password="pw")
    resp1 = Responsible.objects.create(last_name="One", first_name="Zed", user=user1)
    Responsible.objects.create(last_name="Two", first_name="Zed", user=user2)
    status = Status.objects.create(name="In use")
    location = Location.objects.create(name="Home")
    item = _make_item_with_operation(status, location, resp1, "INV-XFER-NOHINT")

    client = Client()
    client.force_login(user1)
    response = client.get(f"/items/{item.pk}/transfer/")
    assert response.status_code == 200
    assert b"server time" not in response.content.lower()


@pytest.mark.django_db
def test_create_transfer_get_shows_existing_pending_transfer() -> None:
    user1 = User.objects.create_user(username="u1", password="pw")
    user2 = User.objects.create_user(username="u2", password="pw")
    resp1 = Responsible.objects.create(last_name="One", first_name="User", user=user1)
    resp2 = Responsible.objects.create(last_name="Two", first_name="User", user=user2)
    status = Status.objects.create(name="In use")
    location = Location.objects.create(name="Home")
    item = _make_item_with_operation(status, location, resp1, "INV-XFER-PENDING")
    PendingTransfer.objects.create(
        item=item, from_responsible=resp1, to_responsible=resp2, notes="hello"
    )

    client = Client()
    client.force_login(user1)
    response = client.get(f"/items/{item.pk}/transfer/")
    assert response.status_code == 200
    # Sender can open the transfer form with prefilled values.
    assert b'name="to_responsible_id"' in response.content
    assert b'name="notes"' in response.content
    assert b"hello" in response.content


@pytest.mark.django_db
def test_create_transfer_get_treats_expired_pending_as_absent() -> None:
    """Past-deadline offers must not appear as an editable pending on the form."""

    user1 = User.objects.create_user(username="u1expget", password="pw")
    user2 = User.objects.create_user(username="u2expget", password="pw")
    resp1 = Responsible.objects.create(last_name="One", first_name="ExpGet", user=user1)
    resp2 = Responsible.objects.create(last_name="Two", first_name="ExpGet", user=user2)
    status = Status.objects.create(name="In use")
    location = Location.objects.create(name="Home")
    item = _make_item_with_operation(status, location, resp1, "INV-XFER-EXP-GET")
    transfer = PendingTransfer.objects.create(
        item=item,
        from_responsible=resp1,
        to_responsible=resp2,
        notes="expired-offer-note",
        expires_at=timezone.now() + timedelta(hours=1),
    )
    PendingTransfer.objects.filter(pk=transfer.pk).update(
        expires_at=timezone.now() - timedelta(seconds=1),
    )

    client = Client()
    client.force_login(user1)
    response = client.get(f"/items/{item.pk}/transfer/")
    assert response.status_code == 200
    assert b"expired-offer-note" not in response.content


@pytest.mark.django_db
@override_settings(INVENTORY_PENDING_TRANSFER_EXPIRATION_HOURS=0)
def test_create_transfer_post_creates_pending_transfer() -> None:
    user1 = User.objects.create_user(username="u1", password="pw")
    user2 = User.objects.create_user(username="u2", password="pw")
    resp1 = Responsible.objects.create(last_name="One", first_name="User", user=user1)
    resp2 = Responsible.objects.create(last_name="Two", first_name="User", user=user2)
    status = Status.objects.create(name="In use")
    location = Location.objects.create(name="Home")
    item = _make_item_with_operation(status, location, resp1, "INV-XFER-CREATE")

    client = Client()
    client.force_login(user1)
    response = client.post(
        f"/items/{item.pk}/transfer/",
        {"to_responsible_id": resp2.pk},
    )
    assert response.status_code == 302

    transfer = PendingTransfer.objects.get(item=item)
    assert transfer.from_responsible == resp1
    assert transfer.to_responsible == resp2
    assert transfer.accepted_at is None
    assert transfer.cancelled_at is None
    assert transfer.expires_at is None


@pytest.mark.django_db
@override_settings(INVENTORY_PENDING_TRANSFER_EXPIRATION_HOURS=0)
def test_create_transfer_post_returns_400_when_create_offer_validation_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    If `create_offer` raises ValidationError (e.g. a concurrent second offer),
    the view must re-render the form with HTTP 400 instead of returning 500.
    """

    def _boom(_cls: type[PendingTransfer], **kwargs: object) -> PendingTransfer:
        raise ValidationError(["Offer rejected.", "Please try again."])

    monkeypatch.setattr(PendingTransfer, "create_offer", classmethod(_boom))

    user1 = User.objects.create_user(username="u1val", password="pw")
    user2 = User.objects.create_user(username="u2val", password="pw")
    resp1 = Responsible.objects.create(last_name="One", first_name="Val", user=user1)
    resp2 = Responsible.objects.create(last_name="Two", first_name="Val", user=user2)
    status = Status.objects.create(name="In use")
    location = Location.objects.create(name="Home")
    item = _make_item_with_operation(status, location, resp1, "INV-XFER-VAL")

    client = Client()
    client.force_login(user1)
    response = client.post(
        f"/items/{item.pk}/transfer/",
        {"to_responsible_id": resp2.pk, "notes": "keep notes"},
    )
    assert response.status_code == 400
    assert b"Offer rejected.; Please try again." in response.content
    assert PendingTransfer.objects.filter(item=item).count() == 0


@pytest.mark.django_db
@override_settings(INVENTORY_PENDING_TRANSFER_EXPIRATION_HOURS=0)
def test_create_offer_duplicate_active_validation_error_formats_for_display() -> None:
    """
    Real model `ValidationError` on a second `create_offer` must collapse to a
    readable template string (same helper as the transfer view).
    """

    user1 = User.objects.create_user(username="dup1", password="pw")
    user2 = User.objects.create_user(username="dup2", password="pw")
    user3 = User.objects.create_user(username="dup3", password="pw")
    resp1 = Responsible.objects.create(last_name="One", first_name="Dup", user=user1)
    resp2 = Responsible.objects.create(last_name="Two", first_name="Dup", user=user2)
    resp3 = Responsible.objects.create(last_name="Three", first_name="Dup", user=user3)
    status = Status.objects.create(name="In use")
    location = Location.objects.create(name="Home")
    item = _make_item_with_operation(status, location, resp1, "INV-XFER-DUP-OFFER")

    PendingTransfer.create_offer(
        item=item,
        from_responsible=resp1,
        to_responsible=resp2,
        expires_at=None,
        notes="",
    )
    with pytest.raises(ValidationError) as exc_info:
        PendingTransfer.create_offer(
            item=item,
            from_responsible=resp1,
            to_responsible=resp3,
            expires_at=None,
            notes="",
        )
    msg = validation_error_user_message(exc_info.value)
    assert "An active transfer already exists for this item" in msg


@pytest.mark.django_db
@override_settings(INVENTORY_PENDING_TRANSFER_EXPIRATION_HOURS=72)
def test_create_transfer_post_sets_expires_at_from_settings() -> None:
    """UI-created offers get `expires_at` when expiration hours setting is positive."""

    user1 = User.objects.create_user(username="u1e", password="pw")
    user2 = User.objects.create_user(username="u2e", password="pw")
    resp1 = Responsible.objects.create(last_name="One", first_name="Expiry", user=user1)
    resp2 = Responsible.objects.create(last_name="Two", first_name="Expiry", user=user2)
    status = Status.objects.create(name="In use")
    location = Location.objects.create(name="Home")
    item = _make_item_with_operation(status, location, resp1, "INV-XFER-EXP")

    client = Client()
    client.force_login(user1)
    before = timezone.now()
    response = client.post(
        f"/items/{item.pk}/transfer/",
        {"to_responsible_id": resp2.pk},
    )
    after = timezone.now()
    assert response.status_code == 302

    transfer = PendingTransfer.objects.get(item=item)
    assert transfer.expires_at is not None
    assert (
        before + timedelta(hours=72)
        <= transfer.expires_at
        <= after + timedelta(hours=72)
    )


@pytest.mark.django_db
@override_settings(INVENTORY_PENDING_TRANSFER_EXPIRATION_HOURS=72)
def test_create_transfer_post_updates_active_offer_when_receiver_changes() -> None:
    """
    Sender POST to the transfer form while an active PendingTransfer exists must hit
    `update_offer`: receiver and notes change, expiry is refreshed when the receiver
    changes (same behaviour as the model, exercised through the view).
    """

    user1 = User.objects.create_user(username="u1upd", password="pw")
    user2 = User.objects.create_user(username="u2upd", password="pw")
    user3 = User.objects.create_user(username="u3upd", password="pw")
    resp1 = Responsible.objects.create(last_name="One", first_name="Upd", user=user1)
    resp2 = Responsible.objects.create(last_name="Two", first_name="Upd", user=user2)
    resp3 = Responsible.objects.create(last_name="Three", first_name="Upd", user=user3)
    status = Status.objects.create(name="In use")
    location = Location.objects.create(name="Home")
    item = _make_item_with_operation(status, location, resp1, "INV-XFER-UPDATE-OFFER")

    transfer = PendingTransfer.objects.create(
        item=item,
        from_responsible=resp1,
        to_responsible=resp2,
        notes="old",
    )

    client = Client()
    client.force_login(user1)
    new_notes = "edited via post"
    slack = timedelta(seconds=5)
    before = timezone.now()
    response = client.post(
        f"/items/{item.pk}/transfer/",
        {"to_responsible_id": resp3.pk, "notes": new_notes},
    )
    after = timezone.now()

    assert response.status_code == 302
    assert response["Location"] == f"/items/{item.pk}/"

    transfer.refresh_from_db()
    assert transfer.to_responsible_id == resp3.pk
    assert transfer.notes == new_notes
    assert PendingTransfer.objects.filter(item=item).count() == 1
    assert transfer.accepted_at is None
    assert transfer.cancelled_at is None

    assert transfer.expires_at is not None
    assert (
        before + timedelta(hours=72) - slack
        <= transfer.expires_at
        <= after + timedelta(hours=72) + slack
    )


@pytest.mark.django_db
@override_settings(INVENTORY_PENDING_TRANSFER_EXPIRATION_HOURS=0)
def test_create_transfer_post_edit_offer_auto_accepts_no_user_receiver() -> None:
    """
    Editing an active offer toward a Responsible without a linked user must
    auto-complete the transfer (same rule as `create_offer` / `update_offer`).
    """

    user1 = User.objects.create_user(username="u1nouserupd", password="pw")
    user2 = User.objects.create_user(username="u2nouserupd", password="pw")
    resp1 = Responsible.objects.create(
        last_name="One", first_name="NoUserUpd", user=user1
    )
    resp2 = Responsible.objects.create(
        last_name="Two", first_name="NoUserUpd", user=user2
    )
    resp3 = Responsible.objects.create(last_name="Three", first_name="NoUserUpd")
    assert resp3.user_id is None

    status = Status.objects.create(name="In use")
    location = Location.objects.create(name="Home")
    item = _make_item_with_operation(status, location, resp1, "INV-XFER-UPD-NOUS")

    PendingTransfer.objects.create(
        item=item,
        from_responsible=resp1,
        to_responsible=resp2,
        notes="was pending",
    )

    client = Client()
    client.force_login(user1)
    response = client.post(
        f"/items/{item.pk}/transfer/",
        {"to_responsible_id": resp3.pk, "notes": "switch to offline receiver"},
    )
    assert response.status_code == 302

    transfer = PendingTransfer.objects.get(item=item)
    transfer.refresh_from_db()
    assert transfer.to_responsible_id == resp3.pk
    assert transfer.notes == "switch to offline receiver"
    assert transfer.accepted_at is not None
    latest = item.operation_set.order_by("-created_at", "-id").first()
    assert latest is not None
    assert latest.responsible_id == resp3.pk


@pytest.mark.django_db
@override_settings(INVENTORY_PENDING_TRANSFER_EXPIRATION_HOURS=0)
def test_create_transfer_auto_accepts_when_receiver_has_no_user() -> None:
    """
    If the receiver Responsible has no linked Django user, the transfer offer must be
    accepted automatically (there is nobody who could confirm it in the UI).
    """

    user_sender = User.objects.create_user(username="sender-auto", password="pw")
    resp_sender = Responsible.objects.create(
        last_name="Sender",
        first_name="Auto",
        user=user_sender,
    )
    resp_receiver = Responsible.objects.create(
        last_name="Receiver", first_name="NoUser"
    )
    assert resp_receiver.user_id is None

    status = Status.objects.create(name="In use")
    location = Location.objects.create(name="Home")
    item = _make_item_with_operation(
        status, location, resp_sender, "INV-XFER-AUTO-ACCEPT"
    )

    client = Client()
    client.force_login(user_sender)
    response = client.post(
        f"/items/{item.pk}/transfer/",
        {"to_responsible_id": resp_receiver.pk},
    )
    assert response.status_code == 302

    transfer = PendingTransfer.objects.get(item=item)
    assert transfer.accepted_at is not None
    assert transfer.cancelled_at is None

    latest = item.operation_set.order_by("-created_at", "-id").first()
    assert latest is not None
    assert latest.responsible == resp_receiver


@pytest.mark.django_db
def test_accept_transfer_requires_receiver_confirmation_and_changes_owner() -> None:
    user_sender = User.objects.create_user(username="sender", password="pw")
    user_receiver = User.objects.create_user(username="receiver", password="pw")
    resp_sender = Responsible.objects.create(
        last_name="Sender", first_name="User", user=user_sender
    )
    resp_receiver = Responsible.objects.create(
        last_name="Receiver", first_name="User", user=user_receiver
    )
    status = Status.objects.create(name="In use")
    location = Location.objects.create(name="Home")
    item = _make_item_with_operation(status, location, resp_sender, "INV-XFER-ACCEPT")

    transfer = PendingTransfer.objects.create(
        item=item,
        from_responsible=resp_sender,
        to_responsible=resp_receiver,
    )

    # Sender cannot accept.
    client_sender = Client()
    client_sender.force_login(user_sender)
    forbidden = client_sender.post(
        f"/transfers/{transfer.pk}/accept/",
        _accept_journal_baseline_post(item),
    )
    assert forbidden.status_code == 404

    # Receiver accepts: ownership changes via a new Operation.
    client_receiver = Client()
    client_receiver.force_login(user_receiver)
    ok = client_receiver.post(
        f"/transfers/{transfer.pk}/accept/",
        _accept_journal_baseline_post(item),
    )
    assert ok.status_code == 302

    transfer.refresh_from_db()
    assert transfer.accepted_at is not None
    assert transfer.cancelled_at is None

    latest = item.operation_set.order_by("-created_at", "-id").first()
    assert latest is not None
    assert latest.responsible == resp_receiver
    assert latest.status == status
    assert latest.location == location

    # Receiver should now see the item on "My items".
    response = client_receiver.get("/")
    assert response.status_code == 200
    assert item.inventory_number.encode("utf-8") in response.content


@pytest.mark.django_db
def test_accept_transfer_returns_404_if_user_has_no_responsible() -> None:
    user = User.objects.create_user(username="u1", password="pw")
    client = Client()
    client.force_login(user)
    response = client.post("/transfers/1/accept/")
    assert response.status_code == 404


@pytest.mark.django_db
def test_cancel_transfer_is_allowed_for_sender_and_receiver() -> None:
    user_sender = User.objects.create_user(username="sender", password="pw")
    user_receiver = User.objects.create_user(username="receiver", password="pw")
    resp_sender = Responsible.objects.create(
        last_name="Sender", first_name="User", user=user_sender
    )
    resp_receiver = Responsible.objects.create(
        last_name="Receiver", first_name="User", user=user_receiver
    )
    status = Status.objects.create(name="In use")
    location = Location.objects.create(name="Home")
    item = _make_item_with_operation(status, location, resp_sender, "INV-XFER-CANCEL")

    transfer = PendingTransfer.objects.create(
        item=item,
        from_responsible=resp_sender,
        to_responsible=resp_receiver,
    )

    client_receiver = Client()
    client_receiver.force_login(user_receiver)
    ok_receiver = client_receiver.post(f"/transfers/{transfer.pk}/cancel/")
    assert ok_receiver.status_code == 302

    transfer.refresh_from_db()
    assert transfer.cancelled_at is not None
    assert transfer.accepted_at is None

    # Reset state: create another transfer for sender cancellation path.
    transfer2 = PendingTransfer.objects.create(
        item=item,
        from_responsible=resp_sender,
        to_responsible=resp_receiver,
    )

    client_sender = Client()
    client_sender.force_login(user_sender)
    ok_sender = client_sender.post(f"/transfers/{transfer2.pk}/cancel/")
    assert ok_sender.status_code == 302

    transfer2.refresh_from_db()
    assert transfer2.cancelled_at is not None
    assert transfer2.accepted_at is None


@pytest.mark.django_db
def test_cancel_transfer_returns_404_if_user_has_no_responsible() -> None:
    user = User.objects.create_user(username="u1", password="pw")
    client = Client()
    client.force_login(user)
    response = client.post("/transfers/1/cancel/")
    assert response.status_code == 404


@pytest.mark.django_db
def test_accept_transfer_returns_404_for_unknown_transfer_id() -> None:
    user = User.objects.create_user(username="u1", password="pw")
    resp = Responsible.objects.create(last_name="Ivanov", first_name="Ivan", user=user)
    client = Client()
    client.force_login(user)
    response = client.post("/transfers/999999/accept/")
    assert response.status_code == 404
    _ = resp


@pytest.mark.django_db
def test_cancel_transfer_returns_404_for_unknown_transfer_id() -> None:
    user = User.objects.create_user(username="u1", password="pw")
    resp = Responsible.objects.create(last_name="Ivanov", first_name="Ivan", user=user)
    client = Client()
    client.force_login(user)
    response = client.post("/transfers/999999/cancel/")
    assert response.status_code == 404
    _ = resp


@pytest.mark.django_db
def test_cancel_transfer_returns_404_if_user_is_not_sender_or_receiver() -> None:
    user_sender = User.objects.create_user(username="sender", password="pw")
    user_receiver = User.objects.create_user(username="receiver", password="pw")
    user_other = User.objects.create_user(username="other", password="pw")
    resp_sender = Responsible.objects.create(
        last_name="Sender", first_name="User", user=user_sender
    )
    resp_receiver = Responsible.objects.create(
        last_name="Receiver", first_name="User", user=user_receiver
    )
    resp_other = Responsible.objects.create(
        last_name="Other", first_name="User", user=user_other
    )
    status = Status.objects.create(name="In use")
    location = Location.objects.create(name="Home")
    item = _make_item_with_operation(status, location, resp_sender, "INV-XFER-FORBID")

    transfer = PendingTransfer.objects.create(
        item=item,
        from_responsible=resp_sender,
        to_responsible=resp_receiver,
    )

    client_other = Client()
    client_other.force_login(user_other)
    response = client_other.post(f"/transfers/{transfer.pk}/cancel/")
    assert response.status_code == 404

    _ = resp_other


@pytest.mark.django_db
def test_accept_transfer_returns_404_if_user_is_not_sender_or_receiver() -> None:
    user_sender = User.objects.create_user(username="acc-snd", password="pw")
    user_receiver = User.objects.create_user(username="acc-rcv", password="pw")
    user_other = User.objects.create_user(username="acc-oth", password="pw")
    resp_sender = Responsible.objects.create(
        last_name="Sender", first_name="Acc", user=user_sender
    )
    resp_receiver = Responsible.objects.create(
        last_name="Receiver", first_name="Acc", user=user_receiver
    )
    resp_other = Responsible.objects.create(
        last_name="Other", first_name="Acc", user=user_other
    )
    status = Status.objects.create(name="In use")
    location = Location.objects.create(name="Home")
    item = _make_item_with_operation(
        status, location, resp_sender, "INV-XFER-ACCEPT-FORBID"
    )
    transfer = PendingTransfer.objects.create(
        item=item,
        from_responsible=resp_sender,
        to_responsible=resp_receiver,
    )

    client_other = Client()
    client_other.force_login(user_other)
    assert (
        client_other.post(
            f"/transfers/{transfer.pk}/accept/",
            _accept_journal_baseline_post(item),
        ).status_code
        == 404
    )

    _ = resp_other


@pytest.mark.django_db
def test_cancel_transfer_warns_when_inactive() -> None:
    user_sender = User.objects.create_user(username="sender", password="pw")
    user_receiver = User.objects.create_user(username="receiver", password="pw")
    resp_sender = Responsible.objects.create(
        last_name="Sender", first_name="User", user=user_sender
    )
    resp_receiver = Responsible.objects.create(
        last_name="Receiver", first_name="User", user=user_receiver
    )
    status = Status.objects.create(name="In use")
    location = Location.objects.create(name="Home")
    item = _make_item_with_operation(
        status, location, resp_sender, "INV-XFER-INACTIVE-CANCEL"
    )
    transfer = PendingTransfer.objects.create(
        item=item,
        from_responsible=resp_sender,
        to_responsible=resp_receiver,
    )
    PendingTransfer.objects.filter(pk=transfer.pk).update(cancelled_at=timezone.now())

    client = Client()
    client.force_login(user_sender)
    response = client.post(f"/transfers/{transfer.pk}/cancel/", follow=True)
    assert response.status_code == 200
    assert response.request["PATH_INFO"] == f"/items/{item.pk}/"
    assert b"This transfer offer is no longer active" in response.content


@pytest.mark.django_db
def test_accept_transfer_surfaces_inactive_message_when_offer_flips_inside_transaction(
    monkeypatch,
) -> None:
    user_sender = User.objects.create_user(username="sender", password="pw")
    user_receiver = User.objects.create_user(username="receiver", password="pw")
    resp_sender = Responsible.objects.create(
        last_name="Sender", first_name="User", user=user_sender
    )
    resp_receiver = Responsible.objects.create(
        last_name="Receiver", first_name="User", user=user_receiver
    )
    status = Status.objects.create(name="In use")
    location = Location.objects.create(name="Home")
    item = _make_item_with_operation(status, location, resp_sender, "INV-XFER-RACE")
    transfer = PendingTransfer.objects.create(
        item=item,
        from_responsible=resp_sender,
        to_responsible=resp_receiver,
    )

    calls = {"n": 0}
    original_prop = PendingTransfer.is_active

    def _fake_is_active(self: PendingTransfer) -> bool:
        calls["n"] += 1
        return calls["n"] == 1

    monkeypatch.setattr(PendingTransfer, "is_active", property(_fake_is_active))
    client = Client()
    client.force_login(user_receiver)
    try:
        post_response = client.post(
            f"/transfers/{transfer.pk}/accept/",
            _accept_journal_baseline_post(item),
            follow=False,
        )
    finally:
        monkeypatch.setattr(PendingTransfer, "is_active", original_prop)

    assert post_response.status_code == 302
    follow = client.get(post_response["Location"])
    assert follow.status_code == 200
    assert b"Transfer is not active" in follow.content


@pytest.mark.django_db
def test_incoming_transfers_lists_offers_for_receiver() -> None:
    user_sender = User.objects.create_user(username="sender", password="pw")
    user_receiver = User.objects.create_user(username="receiver", password="pw")
    resp_sender = Responsible.objects.create(
        last_name="Sender", first_name="User", user=user_sender
    )
    resp_receiver = Responsible.objects.create(
        last_name="Receiver", first_name="User", user=user_receiver
    )
    status = Status.objects.create(name="In use")
    location = Location.objects.create(name="Home")
    item = _make_item_with_operation(status, location, resp_sender, "INV-XFER-INBOX")
    PendingTransfer.objects.create(
        item=item,
        from_responsible=resp_sender,
        to_responsible=resp_receiver,
    )

    client = Client()
    client.force_login(user_receiver)
    response = client.get("/")
    assert response.status_code == 200
    assert item.inventory_number.encode("utf-8") in response.content


@pytest.mark.django_db
def test_outgoing_transfers_lists_offers_for_sender() -> None:
    user_sender = User.objects.create_user(username="sender", password="pw")
    user_receiver = User.objects.create_user(username="receiver", password="pw")
    resp_sender = Responsible.objects.create(
        last_name="Sender", first_name="User", user=user_sender
    )
    resp_receiver = Responsible.objects.create(
        last_name="Receiver", first_name="User", user=user_receiver
    )
    status = Status.objects.create(name="In use")
    location = Location.objects.create(name="Home")
    item = _make_item_with_operation(status, location, resp_sender, "INV-XFER-OUTBOX")
    PendingTransfer.objects.create(
        item=item,
        from_responsible=resp_sender,
        to_responsible=resp_receiver,
    )

    client = Client()
    client.force_login(user_sender)
    response = client.get("/")
    assert response.status_code == 200
    assert item.inventory_number.encode("utf-8") in response.content


@pytest.mark.django_db
def test_my_items_does_not_duplicate_item_between_owned_and_outgoing_transfer() -> None:
    user_sender = User.objects.create_user(username="sender", password="pw")
    user_receiver = User.objects.create_user(username="receiver", password="pw")
    resp_sender = Responsible.objects.create(
        last_name="Sender", first_name="User", user=user_sender
    )
    resp_receiver = Responsible.objects.create(
        last_name="Receiver", first_name="User", user=user_receiver
    )
    status = Status.objects.create(name="In use")
    location = Location.objects.create(name="Home")
    item = _make_item_with_operation(status, location, resp_sender, "INV-XFER-NODUPE")
    PendingTransfer.objects.create(
        item=item,
        from_responsible=resp_sender,
        to_responsible=resp_receiver,
    )

    client = Client()
    client.force_login(user_sender)
    response = client.get("/")
    assert response.status_code == 200
    # The transfer card is rendered as an item-card with a modifier class.
    # The same item must not be rendered again as a plain owned item-card.
    assert (
        response.content.count(b'class="item-card item-card--outgoing-transfer"') == 1
    )
    assert response.content.count(b'class="item-card"') == 0


@pytest.mark.django_db
def test_my_items_lists_owned_row_when_pending_transfer_is_expired() -> None:
    """
    Expired offers must not hide the item from the owned list or show as outgoing
    transfer cards (same non-expired semantics as `PendingTransfer.is_active`).
    """

    user_sender = User.objects.create_user(username="sndexp", password="pw")
    user_receiver = User.objects.create_user(username="rcvexp", password="pw")
    resp_sender = Responsible.objects.create(
        last_name="Sender", first_name="Exp", user=user_sender
    )
    resp_receiver = Responsible.objects.create(
        last_name="Receiver", first_name="Exp", user=user_receiver
    )
    status = Status.objects.create(name="In use")
    location = Location.objects.create(name="Home")
    item = _make_item_with_operation(status, location, resp_sender, "INV-XFER-EXP-OWN")
    transfer = PendingTransfer.objects.create(
        item=item,
        from_responsible=resp_sender,
        to_responsible=resp_receiver,
        expires_at=timezone.now() + timedelta(hours=1),
    )
    PendingTransfer.objects.filter(pk=transfer.pk).update(
        expires_at=timezone.now() - timedelta(seconds=1),
    )

    client = Client()
    client.force_login(user_sender)
    response = client.get("/")
    assert response.status_code == 200
    assert b"INV-XFER-EXP-OWN" in response.content
    assert b'class="item-card item-card--outgoing-transfer"' not in response.content


@pytest.mark.django_db
def test_transfers_page_is_removed() -> None:
    user = User.objects.create_user(username="u1", password="pw")
    client = Client()
    client.force_login(user)
    assert client.get("/transfers/").status_code == 404


@pytest.mark.django_db
def test_transfers_incoming_and_outgoing_urls_are_removed() -> None:
    user = User.objects.create_user(username="u1", password="pw")
    Responsible.objects.create(last_name="Ivanov", first_name="Ivan", user=user)
    client = Client()
    client.force_login(user)
    assert client.get("/transfers/incoming/").status_code == 404
    assert client.get("/transfers/outgoing/").status_code == 404


@pytest.mark.django_db
def test_create_transfer_post_returns_400_for_missing_or_invalid_receiver() -> None:
    user1 = User.objects.create_user(username="u1", password="pw")
    resp1 = Responsible.objects.create(last_name="One", first_name="User", user=user1)
    status = Status.objects.create(name="In use")
    location = Location.objects.create(name="Home")
    item = _make_item_with_operation(status, location, resp1, "INV-XFER-POST-404")

    client = Client()
    client.force_login(user1)

    missing = client.post(f"/items/{item.pk}/transfer/", {})
    assert missing.status_code == 400

    invalid = client.post(f"/items/{item.pk}/transfer/", {"to_responsible_id": "nope"})
    assert invalid.status_code == 400

    self_id = client.post(
        f"/items/{item.pk}/transfer/", {"to_responsible_id": resp1.pk}
    )
    assert self_id.status_code == 400


@pytest.mark.django_db
def test_accept_and_cancel_transfer_require_post_method() -> None:
    user_sender = User.objects.create_user(username="sender", password="pw")
    user_receiver = User.objects.create_user(username="receiver", password="pw")
    resp_sender = Responsible.objects.create(
        last_name="Sender", first_name="User", user=user_sender
    )
    resp_receiver = Responsible.objects.create(
        last_name="Receiver", first_name="User", user=user_receiver
    )
    status = Status.objects.create(name="In use")
    location = Location.objects.create(name="Home")
    item = _make_item_with_operation(status, location, resp_sender, "INV-XFER-METHOD")
    transfer = PendingTransfer.objects.create(
        item=item, from_responsible=resp_sender, to_responsible=resp_receiver
    )

    client_receiver = Client()
    client_receiver.force_login(user_receiver)
    assert client_receiver.get(f"/transfers/{transfer.pk}/accept/").status_code == 404

    client_sender = Client()
    client_sender.force_login(user_sender)
    assert client_sender.get(f"/transfers/{transfer.pk}/cancel/").status_code == 404


@pytest.mark.django_db
def test_accept_transfer_warns_when_expired() -> None:
    user_sender = User.objects.create_user(username="sender", password="pw")
    user_receiver = User.objects.create_user(username="receiver", password="pw")
    resp_sender = Responsible.objects.create(
        last_name="Sender", first_name="User", user=user_sender
    )
    resp_receiver = Responsible.objects.create(
        last_name="Receiver", first_name="User", user=user_receiver
    )
    status = Status.objects.create(name="In use")
    location = Location.objects.create(name="Home")
    item = _make_item_with_operation(
        status, location, resp_sender, "INV-XFER-EXPIRE-404"
    )
    transfer = PendingTransfer.objects.create(
        item=item, from_responsible=resp_sender, to_responsible=resp_receiver
    )

    # Force expiry at the DB level (model clean forbids creating already-expired
    # transfers).
    PendingTransfer.objects.filter(pk=transfer.pk).update(
        expires_at=timezone.now() - timedelta(seconds=1)
    )

    client_receiver = Client()
    client_receiver.force_login(user_receiver)
    response = client_receiver.post(f"/transfers/{transfer.pk}/accept/", follow=True)
    assert response.status_code == 200
    assert response.request["PATH_INFO"] == "/"
    assert b"This transfer offer is no longer active" in response.content


@pytest.mark.django_db
def test_item_history_hides_pending_transfer_from_former_owner() -> None:
    user_owner = User.objects.create_user(username="owner", password="pw")
    user_receiver = User.objects.create_user(username="receiver", password="pw")
    user_former = User.objects.create_user(username="former", password="pw")
    resp_owner = Responsible.objects.create(
        last_name="Owner", first_name="User", user=user_owner
    )
    resp_receiver = Responsible.objects.create(
        last_name="Receiver", first_name="User", user=user_receiver
    )
    resp_former = Responsible.objects.create(
        last_name="Former", first_name="User", user=user_former
    )

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

    item = Item.objects.create(inventory_number="INV-XFER-HIDE", device=device)
    Operation.objects.create(
        item=item,
        status=status,
        responsible=resp_former,
        location=location,
        notes="former",
    )
    Operation.objects.create(
        item=item,
        status=status,
        responsible=resp_owner,
        location=location,
        notes="owner",
    )

    PendingTransfer.objects.create(
        item=item, from_responsible=resp_owner, to_responsible=resp_receiver
    )

    client = Client()
    client.force_login(user_former)
    response = client.get(f"/items/{item.pk}/")
    assert response.status_code == 200
    assert b"Pending transfer" not in response.content


@pytest.mark.django_db
def test_item_history_shows_pending_transfer_to_owner() -> None:
    user_owner = User.objects.create_user(username="owner", password="pw")
    user_receiver = User.objects.create_user(username="receiver", password="pw")
    resp_owner = Responsible.objects.create(
        last_name="Owner", first_name="User", user=user_owner
    )
    resp_receiver = Responsible.objects.create(
        last_name="Receiver", first_name="User", user=user_receiver
    )

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
    item = Item.objects.create(inventory_number="INV-XFER-SHOW", device=device)
    Operation.objects.create(
        item=item, status=status, responsible=resp_owner, location=location
    )

    PendingTransfer.objects.create(
        item=item,
        from_responsible=resp_owner,
        to_responsible=resp_receiver,
    )

    client = Client()
    client.force_login(user_owner)
    response = client.get(f"/items/{item.pk}/")
    assert response.status_code == 200
    assert (
        b"Outgoing transfer for" in response.content
        or "Исходящая передача".encode("utf-8") in response.content
    )
    assert (
        reverse("inventory:create-transfer", kwargs={"item_id": item.pk}).encode(
            "utf-8"
        )
        in response.content
    )


@pytest.mark.django_db
def test_item_history_allows_receiver_to_view_item_with_pending_transfer() -> None:
    user_owner = User.objects.create_user(username="owner", password="pw")
    user_receiver = User.objects.create_user(username="receiver", password="pw")
    resp_owner = Responsible.objects.create(
        last_name="Owner", first_name="User", user=user_owner
    )
    resp_receiver = Responsible.objects.create(
        last_name="Receiver", first_name="User", user=user_receiver
    )

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
    item = Item.objects.create(inventory_number="INV-XFER-RECV", device=device)
    Operation.objects.create(
        item=item,
        status=status,
        responsible=resp_owner,
        location=location,
        notes="owner",
    )
    Operation.objects.create(
        item=item,
        status=status,
        responsible=resp_owner,
        location=location,
        notes="newest",
    )

    PendingTransfer.objects.create(
        item=item,
        from_responsible=resp_owner,
        to_responsible=resp_receiver,
    )

    client = Client()
    client.force_login(user_receiver)
    response = client.get(f"/items/{item.pk}/")
    assert response.status_code == 200
    assert (
        b"Incoming transfer from" in response.content
        or "Входящая передача".encode("utf-8") in response.content
    )
    assert b"newest" in response.content
    assert b"owner" in response.content


@pytest.mark.django_db
def test_item_history_shows_pending_transfer_notes_when_present() -> None:
    user_owner = User.objects.create_user(username="owner-notes", password="pw")
    user_receiver = User.objects.create_user(username="receiver-notes", password="pw")
    resp_owner = Responsible.objects.create(
        last_name="Owner", first_name="Notes", user=user_owner
    )
    resp_receiver = Responsible.objects.create(
        last_name="Receiver", first_name="Notes", user=user_receiver
    )

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
    item = Item.objects.create(inventory_number="INV-XFER-NOTES", device=device)
    Operation.objects.create(
        item=item,
        status=status,
        responsible=resp_owner,
        location=location,
    )

    note = "Handle with care"
    PendingTransfer.objects.create(
        item=item,
        from_responsible=resp_owner,
        to_responsible=resp_receiver,
        notes=note,
    )

    client = Client()
    client.force_login(user_owner)
    response = client.get(f"/items/{item.pk}/")
    assert response.status_code == 200
    assert note.encode("utf-8") in response.content


@pytest.mark.django_db
def test_create_transfer_post_returns_404_when_pending_sender_mismatches_owner() -> (
    None
):
    """
    ``POST`` rejects a pending offer whose ``from_responsible`` is not the current
    owner (append-only journal can move ownership past a stale pending row).
    """

    user_a = User.objects.create_user(username="a-post-404", password="pw")
    user_b = User.objects.create_user(username="b-post-404", password="pw")
    user_c = User.objects.create_user(username="c-post-404", password="pw")
    resp_a = Responsible.objects.create(last_name="A", first_name="Post", user=user_a)
    resp_b = Responsible.objects.create(last_name="B", first_name="Post", user=user_b)
    resp_c = Responsible.objects.create(last_name="C", first_name="Post", user=user_c)
    status = Status.objects.create(name="In stock")
    location = Location.objects.create(name="Moscow")
    item = _make_item_with_operation(status, location, resp_a, "INV-XFER-POST-MISMATCH")
    PendingTransfer.objects.create(
        item=item,
        from_responsible=resp_a,
        to_responsible=resp_c,
    )
    Operation.objects.create(
        item=item,
        status=status,
        responsible=resp_b,
        location=location,
    )

    client = Client()
    client.force_login(user_b)
    response = client.post(
        reverse("inventory:create-transfer", kwargs={"item_id": item.pk}),
        {"to_responsible_id": str(resp_c.pk), "notes": "n"},
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_create_transfer_get_read_only_card_when_pending_sender_mismatches_owner() -> (
    None
):
    """
    Current owner sees the read-only transfer card when a stale pending row still
    names a different ``from_responsible`` (same invariant as ``POST``).
    """

    user_a = User.objects.create_user(username="a-get-card", password="pw")
    user_b = User.objects.create_user(username="b-get-card", password="pw")
    user_c = User.objects.create_user(username="c-get-card", password="pw")
    resp_a = Responsible.objects.create(last_name="A", first_name="Get", user=user_a)
    resp_b = Responsible.objects.create(last_name="B", first_name="Get", user=user_b)
    resp_c = Responsible.objects.create(last_name="C", first_name="Get", user=user_c)
    status = Status.objects.create(name="In stock")
    location = Location.objects.create(name="Moscow")
    item = _make_item_with_operation(status, location, resp_a, "INV-XFER-GET-MISMATCH")
    PendingTransfer.objects.create(
        item=item,
        from_responsible=resp_a,
        to_responsible=resp_c,
    )
    Operation.objects.create(
        item=item,
        status=status,
        responsible=resp_b,
        location=location,
    )

    client = Client()
    client.force_login(user_b)
    response = client.get(
        reverse("inventory:create-transfer", kwargs={"item_id": item.pk})
    )
    assert response.status_code == 200
    assert b"item-card--outgoing-transfer" in response.content
    assert b'name="to_responsible_id"' not in response.content


@pytest.mark.django_db
def test_create_transfer_post_raises_if_parse_returns_receiver_without_response() -> (
    None
):
    """
    ``parse_transfer_receiver_or_render_error`` must never return ``(None, None)``;
    this test locks that contract for the pending-offer ``POST`` branch.
    """

    user_b = User.objects.create_user(username="b-parse-inv", password="pw")
    user_c = User.objects.create_user(username="c-parse-inv", password="pw")
    resp_b = Responsible.objects.create(last_name="B", first_name="Inv", user=user_b)
    resp_c = Responsible.objects.create(last_name="C", first_name="Inv", user=user_c)
    status = Status.objects.create(name="In stock")
    location = Location.objects.create(name="Moscow")
    item = _make_item_with_operation(status, location, resp_b, "INV-XFER-PARSE-INV")
    PendingTransfer.objects.create(
        item=item,
        from_responsible=resp_b,
        to_responsible=resp_c,
    )

    client = Client()
    client.force_login(user_b)
    with patch(
        "inventory.views.transfer_views.parse_transfer_receiver_or_render_error",
        return_value=(None, None),
    ):
        with pytest.raises(AssertionError):
            client.post(
                reverse("inventory:create-transfer", kwargs={"item_id": item.pk}),
                {"to_responsible_id": str(resp_c.pk), "notes": "n"},
            )


@pytest.mark.django_db
def test_create_transfer_post_new_offer_raises_if_parse_returns_broken_tuple() -> None:
    """Same invariant as the pending-offer branch, but for the initial ``POST`` path."""

    user = User.objects.create_user(username="parse-new", password="pw")
    resp = Responsible.objects.create(last_name="Own", first_name="Er", user=user)
    resp_other = Responsible.objects.create(last_name="Oth", first_name="Er")
    status = Status.objects.create(name="In stock")
    location = Location.objects.create(name="Moscow")
    item = _make_item_with_operation(status, location, resp, "INV-XFER-PARSE-NEW")

    client = Client()
    client.force_login(user)
    with patch(
        "inventory.views.transfer_views.parse_transfer_receiver_or_render_error",
        return_value=(None, None),
    ):
        with pytest.raises(AssertionError):
            client.post(
                reverse("inventory:create-transfer", kwargs={"item_id": item.pk}),
                {"to_responsible_id": str(resp_other.pk), "notes": "n"},
            )


@pytest.mark.django_db
def test_create_transfer_post_invalid_receiver_pending_edit() -> None:
    """Parse errors short-circuit before ``update_offer`` (pending-offer ``POST``)."""

    user_b = User.objects.create_user(username="b-inv-pend", password="pw")
    user_c = User.objects.create_user(username="c-inv-pend", password="pw")
    resp_b = Responsible.objects.create(last_name="B", first_name="Inv", user=user_b)
    resp_c = Responsible.objects.create(last_name="C", first_name="Inv", user=user_c)
    status = Status.objects.create(name="In stock")
    location = Location.objects.create(name="Moscow")
    item = _make_item_with_operation(status, location, resp_b, "INV-XFER-INV-PEND")
    PendingTransfer.objects.create(
        item=item,
        from_responsible=resp_b,
        to_responsible=resp_c,
    )

    client = Client()
    client.force_login(user_b)
    response = client.post(
        reverse("inventory:create-transfer", kwargs={"item_id": item.pk}),
        {"to_responsible_id": "not-an-int", "notes": "n"},
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_create_transfer_post_update_offer_validation_error() -> None:
    user_owner = User.objects.create_user(username="own-upd-val", password="pw")
    user_recv1 = User.objects.create_user(username="r1-upd-val", password="pw")
    user_recv2 = User.objects.create_user(username="r2-upd-val", password="pw")
    resp_owner = Responsible.objects.create(
        last_name="Own", first_name="Upd", user=user_owner
    )
    resp_r1 = Responsible.objects.create(
        last_name="R", first_name="One", user=user_recv1
    )
    resp_r2 = Responsible.objects.create(
        last_name="R", first_name="Two", user=user_recv2
    )
    status = Status.objects.create(name="In stock")
    location = Location.objects.create(name="Moscow")
    item = _make_item_with_operation(status, location, resp_owner, "INV-XFER-UPD-VAL")
    PendingTransfer.objects.create(
        item=item,
        from_responsible=resp_owner,
        to_responsible=resp_r1,
    )

    client = Client()
    client.force_login(user_owner)
    with patch.object(
        PendingTransfer,
        "update_offer",
        side_effect=ValidationError("domain failure"),
    ):
        response = client.post(
            reverse("inventory:create-transfer", kwargs={"item_id": item.pk}),
            {"to_responsible_id": str(resp_r2.pk), "notes": "n"},
        )
    assert response.status_code == 400


@pytest.mark.django_db
def test_cancel_transfer_surfaces_validation_error_message() -> None:
    user_sender = User.objects.create_user(username="snd-can-val", password="pw")
    user_receiver = User.objects.create_user(username="rcv-can-val", password="pw")
    resp_sender = Responsible.objects.create(
        last_name="S", first_name="Can", user=user_sender
    )
    resp_receiver = Responsible.objects.create(
        last_name="R", first_name="Can", user=user_receiver
    )
    status = Status.objects.create(name="In stock")
    location = Location.objects.create(name="Moscow")
    item = _make_item_with_operation(status, location, resp_sender, "INV-XFER-CAN-VAL")
    transfer = PendingTransfer.objects.create(
        item=item,
        from_responsible=resp_sender,
        to_responsible=resp_receiver,
    )

    client = Client()
    client.force_login(user_sender)
    with patch.object(
        PendingTransfer,
        "cancel",
        side_effect=ValidationError("inactive"),
    ):
        response = client.post(
            reverse("inventory:cancel-transfer", kwargs={"transfer_id": transfer.pk}),
            follow=True,
        )
    assert response.status_code == 200
    assert b"inactive" in response.content


@pytest.mark.django_db
def test_accept_transfer_surfaces_validation_error_message() -> None:
    user_sender = User.objects.create_user(username="snd-acc-val", password="pw")
    user_receiver = User.objects.create_user(username="rcv-acc-val", password="pw")
    resp_sender = Responsible.objects.create(
        last_name="S", first_name="Acc", user=user_sender
    )
    resp_receiver = Responsible.objects.create(
        last_name="R", first_name="Acc", user=user_receiver
    )
    status = Status.objects.create(name="In stock")
    location = Location.objects.create(name="Moscow")
    item = _make_item_with_operation(status, location, resp_sender, "INV-XFER-ACC-VAL")
    transfer = PendingTransfer.objects.create(
        item=item,
        from_responsible=resp_sender,
        to_responsible=resp_receiver,
    )

    client = Client()
    client.force_login(user_receiver)
    with patch.object(
        PendingTransfer,
        "accept",
        side_effect=ValidationError("cannot accept"),
    ):
        response = client.post(
            reverse("inventory:accept-transfer", kwargs={"transfer_id": transfer.pk}),
            _accept_journal_baseline_post(item),
            follow=True,
        )
    assert response.status_code == 200
    assert b"cannot accept" in response.content


@pytest.mark.django_db
def test_accept_transfer_shows_error_when_sender_no_longer_holds_item() -> None:
    """
    Stale pending row: journal head moved past sender; receiver sees a flash error.
    """

    user_sender = User.objects.create_user(username="snd-stale", password="pw")
    user_receiver = User.objects.create_user(username="rcv-stale", password="pw")
    user_other = User.objects.create_user(username="oth-stale", password="pw")
    resp_sender = Responsible.objects.create(
        last_name="S", first_name="Stale", user=user_sender
    )
    resp_receiver = Responsible.objects.create(
        last_name="R", first_name="Stale", user=user_receiver
    )
    resp_other = Responsible.objects.create(
        last_name="O", first_name="Stale", user=user_other
    )
    status = Status.objects.create(name="In stock")
    location = Location.objects.create(name="Moscow")
    item = _make_item_with_operation(status, location, resp_sender, "INV-XFER-STALE-V")
    transfer = PendingTransfer.objects.create(
        item=item,
        from_responsible=resp_sender,
        to_responsible=resp_receiver,
    )
    Operation.objects.create(
        item=item,
        status=status,
        responsible=resp_other,
        location=location,
    )

    client = Client()
    client.force_login(user_receiver)
    response = client.post(
        reverse("inventory:accept-transfer", kwargs={"transfer_id": transfer.pk}),
        _accept_journal_baseline_post(item),
        follow=True,
    )
    assert response.status_code == 200
    assert b"sender no longer holds the item" in response.content
    transfer.refresh_from_db()
    assert transfer.accepted_at is None


@pytest.mark.django_db
def test_accept_transfer_rejects_non_numeric_journal_baseline() -> None:
    user_sender = User.objects.create_user(username="snd-bl-bad", password="pw")
    user_receiver = User.objects.create_user(username="rcv-bl-bad", password="pw")
    resp_sender = Responsible.objects.create(
        last_name="S", first_name="Bad", user=user_sender
    )
    resp_receiver = Responsible.objects.create(
        last_name="R", first_name="Bad", user=user_receiver
    )
    status = Status.objects.create(name="In stock")
    location = Location.objects.create(name="Moscow")
    item = _make_item_with_operation(
        status, location, resp_sender, "INV-XFER-BL-BADNUM"
    )
    transfer = PendingTransfer.objects.create(
        item=item,
        from_responsible=resp_sender,
        to_responsible=resp_receiver,
    )

    client = Client()
    client.force_login(user_receiver)
    response = client.post(
        reverse("inventory:accept-transfer", kwargs={"transfer_id": transfer.pk}),
        {"journal_head_operation_id": "not-an-int"},
        follow=True,
    )
    assert response.status_code == 200
    assert b"Refresh the page" in response.content
    transfer.refresh_from_db()
    assert transfer.accepted_at is None


@pytest.mark.django_db
def test_accept_transfer_rejects_missing_journal_baseline() -> None:
    user_sender = User.objects.create_user(username="snd-bl-miss", password="pw")
    user_receiver = User.objects.create_user(username="rcv-bl-miss", password="pw")
    resp_sender = Responsible.objects.create(
        last_name="S", first_name="Bl", user=user_sender
    )
    resp_receiver = Responsible.objects.create(
        last_name="R", first_name="Bl", user=user_receiver
    )
    status = Status.objects.create(name="In stock")
    location = Location.objects.create(name="Moscow")
    item = _make_item_with_operation(status, location, resp_sender, "INV-XFER-BL-MISS")
    transfer = PendingTransfer.objects.create(
        item=item,
        from_responsible=resp_sender,
        to_responsible=resp_receiver,
    )

    client = Client()
    client.force_login(user_receiver)
    response = client.post(
        reverse("inventory:accept-transfer", kwargs={"transfer_id": transfer.pk}),
        follow=True,
    )
    assert response.status_code == 200
    assert b"Refresh the page" in response.content
    transfer.refresh_from_db()
    assert transfer.accepted_at is None


@pytest.mark.django_db
def test_accept_transfer_rejects_stale_journal_baseline() -> None:
    user_sender = User.objects.create_user(username="snd-bl-old", password="pw")
    user_receiver = User.objects.create_user(username="rcv-bl-old", password="pw")
    resp_sender = Responsible.objects.create(
        last_name="S", first_name="Old", user=user_sender
    )
    resp_receiver = Responsible.objects.create(
        last_name="R", first_name="Old", user=user_receiver
    )
    status = Status.objects.create(name="In stock")
    loc_a = Location.objects.create(name="A")
    loc_b = Location.objects.create(name="B")
    item = _make_item_with_operation(status, loc_a, resp_sender, "INV-XFER-BL-STALE")
    stale_id = Operation.latest_operation_id_for_item(item.pk)
    assert stale_id is not None
    transfer = PendingTransfer.objects.create(
        item=item,
        from_responsible=resp_sender,
        to_responsible=resp_receiver,
    )
    item.change_location(responsible=resp_sender, location=loc_b, notes="move")

    client = Client()
    client.force_login(user_receiver)
    response = client.post(
        reverse("inventory:accept-transfer", kwargs={"transfer_id": transfer.pk}),
        {"journal_head_operation_id": str(stale_id)},
        follow=True,
    )
    assert response.status_code == 200
    assert b"Refresh the page" in response.content
    transfer.refresh_from_db()
    assert transfer.accepted_at is None


@pytest.mark.django_db
def test_accept_transfer_stale_baseline_goes_my_items_when_no_history_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_sender = User.objects.create_user(username="snd-bl-nctx", password="pw")
    user_receiver = User.objects.create_user(username="rcv-bl-nctx", password="pw")
    resp_sender = Responsible.objects.create(
        last_name="S", first_name="Nctx", user=user_sender
    )
    resp_receiver = Responsible.objects.create(
        last_name="R", first_name="Nctx", user=user_receiver
    )
    status = Status.objects.create(name="In stock")
    loc_a = Location.objects.create(name="A")
    loc_b = Location.objects.create(name="B")
    item = _make_item_with_operation(status, loc_a, resp_sender, "INV-XFER-BL-NCTX")
    stale_id = Operation.latest_operation_id_for_item(item.pk)
    assert stale_id is not None
    transfer = PendingTransfer.objects.create(
        item=item,
        from_responsible=resp_sender,
        to_responsible=resp_receiver,
    )
    item.change_location(responsible=resp_sender, location=loc_b, notes="move")

    monkeypatch.setattr(
        "inventory.views.transfer_views.resolve_item_history_context",
        lambda *args, **kwargs: None,
    )

    client = Client()
    client.force_login(user_receiver)
    response = client.post(
        reverse("inventory:accept-transfer", kwargs={"transfer_id": transfer.pk}),
        {"journal_head_operation_id": str(stale_id)},
        follow=True,
    )
    assert response.status_code == 200
    assert response.request["PATH_INFO"] == "/"
    assert b"Refresh the page" in response.content


@pytest.mark.django_db
def test_accept_transfer_when_journal_deleted_shows_error() -> None:
    user_sender = User.objects.create_user(username="snd-bl-emp", password="pw")
    user_receiver = User.objects.create_user(username="rcv-bl-emp", password="pw")
    resp_sender = Responsible.objects.create(
        last_name="S", first_name="Emp", user=user_sender
    )
    resp_receiver = Responsible.objects.create(
        last_name="R", first_name="Emp", user=user_receiver
    )
    status = Status.objects.create(name="In stock")
    location = Location.objects.create(name="Moscow")
    item = _make_item_with_operation(status, location, resp_sender, "INV-XFER-BL-EMPTY")
    transfer = PendingTransfer.objects.create(
        item=item,
        from_responsible=resp_sender,
        to_responsible=resp_receiver,
    )
    Operation.objects.filter(item=item).delete()

    client = Client()
    client.force_login(user_receiver)
    response = client.post(
        reverse("inventory:accept-transfer", kwargs={"transfer_id": transfer.pk}),
        {"journal_head_operation_id": "1"},
        follow=True,
    )
    assert response.status_code == 200
    assert response.request["PATH_INFO"] == "/"
    assert b"without operations" in response.content
    transfer.refresh_from_db()
    assert transfer.accepted_at is None


@pytest.mark.django_db
def test_item_history_includes_accept_journal_baseline_for_receiver() -> None:
    user_sender = User.objects.create_user(username="snd-hid", password="pw")
    user_receiver = User.objects.create_user(username="rcv-hid", password="pw")
    resp_sender = Responsible.objects.create(
        last_name="S", first_name="Hid", user=user_sender
    )
    resp_receiver = Responsible.objects.create(
        last_name="R", first_name="Hid", user=user_receiver
    )
    status = Status.objects.create(name="In stock")
    location = Location.objects.create(name="Moscow")
    item = _make_item_with_operation(status, location, resp_sender, "INV-XFER-HIDDEN")
    PendingTransfer.objects.create(
        item=item,
        from_responsible=resp_sender,
        to_responsible=resp_receiver,
    )
    head = Operation.latest_operation_id_for_item(item.pk)
    assert head is not None

    client = Client()
    client.force_login(user_receiver)
    response = client.get(f"/items/{item.pk}/")
    assert response.status_code == 200
    assert b"journal_head_operation_id" in response.content
    assert str(head).encode("utf-8") in response.content
